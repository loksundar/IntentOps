# src/baselines/ner_bilstm_crf.py
import json, math, random
from pathlib import Path
import numpy as np
import torch
from torch import nn
from TorchCRF import CRF

SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

DATA = Path("data/processed/wnut2017")
LMAP = json.loads(Path("data/processed/label_maps/ner_label_map.json").read_text(encoding="utf-8"))
WORDV = json.loads(Path("data/processed/tokenizers/word_vocab.json").read_text(encoding="utf-8"))

TAGS = LMAP["tags"]; TAG2ID = LMAP["tag2id"]
PAD_TAG = "O"; PAD_TAG_ID = TAG2ID.get(PAD_TAG, 0)

PAD, UNK = "<pad>", "<unk>"
WORD2ID = WORDV["word2id"]; PAD_ID, UNK_ID = WORD2ID[PAD], WORD2ID[UNK]

EMB_DIM = 100
HID_DIM = 128
EPOCHS = 6
BATCH = 32
LR = 1e-3
MAXLEN = 120  # clip long tweets

ART_DIR = Path("artifacts/baselines/ner"); ART_DIR.mkdir(parents=True, exist_ok=True)

def read_jsonl(p: Path):
    for line in p.open(encoding="utf-8"):
        yield json.loads(line)

def encode(tokens):
    ids = [WORD2ID.get(t, UNK_ID) for t in tokens[:MAXLEN]]
    return ids

def pad_batch(seqs, pad_id):
    maxlen = max(len(s) for s in seqs)
    return [s + [pad_id]*(maxlen-len(s)) for s in seqs], maxlen

class BiLSTM_CRF(nn.Module):
    def __init__(self, vocab_size, tagset_size):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, EMB_DIM, padding_idx=PAD_ID)
        self.lstm = nn.LSTM(EMB_DIM, HID_DIM//2, num_layers=1, bidirectional=True, batch_first=True)
        self.fc = nn.Linear(HID_DIM, tagset_size)
        self.crf = CRF(tagset_size, batch_first=True)

    def forward(self, x, mask):
        emb = self.emb(x)
        out,_ = self.lstm(emb)
        emissions = self.fc(out)
        return emissions

def batch_iter(split):
    data = list(read_jsonl(DATA/f"{split}.jsonl"))
    # shuffle only for train
    if split == "train":
        random.shuffle(data)
    for i in range(0, len(data), BATCH):
        batch = data[i:i+BATCH]
        toks = [ex["tokens"] for ex in batch]
        tags = [ex["tags"] for ex in batch]
        x = [encode(ts) for ts in toks]
        y = [[TAG2ID.get(t, PAD_TAG_ID) for t in ts[:MAXLEN]] for ts in tags]
        x, _ = pad_batch(x, PAD_ID)
        y, maxlen = pad_batch(y, PAD_TAG_ID)
        mask = [[1 if j < len(batch[k]["tokens"]) and j < MAXLEN else 0 for j in range(maxlen)] for k in range(len(batch))]
        yield torch.tensor(x, dtype=torch.long), torch.tensor(y, dtype=torch.long), torch.tensor(mask, dtype=torch.bool)

def train_epoch(model, opt):
    model.train()
    total = 0.0
    for x, y, mask in batch_iter("train"):
        opt.zero_grad()
        emissions = model(x, mask)
        loss = -model.crf(emissions, y, mask=mask, reduction="mean")
        loss.backward(); opt.step()
        total += loss.item()
    return total

@torch.no_grad()
def evaluate(model, split):
    model.eval()
    all_true, all_pred = [], []
    for x, y, mask in batch_iter(split):
        emissions = model(x, mask)
        pred = model.crf.decode(emissions, mask=mask)
        # flatten masked tokens
        for i in range(len(pred)):
            #m = mask[i].cpu().numpy().astype(bool)
            #y_i = y[i].cpu().numpy()[m]
            #p_i = np.array(pred[i])[m]
            L = int(mask[i].sum().item())  # true length for this sequence
            y_i = y[i, :L].cpu().numpy()   # slice gold to true length
            p_i = np.asarray(pred[i])

            all_true.extend(y_i.tolist())
            all_pred.extend(p_i.tolist())
    # micro-F1 over all tokens
    from sklearn.metrics import f1_score
    f1 = f1_score(all_true, all_pred, average="micro")
    return f1

def main():
    vocab_size = len(WORD2ID)
    tagset_size = len(TAGS)
    model = BiLSTM_CRF(vocab_size, tagset_size)
    opt = torch.optim.AdamW(model.parameters(), lr=LR)

    best_val = -1.0
    history = []
    for ep in range(1, EPOCHS+1):
        loss = train_epoch(model, opt)
        f1_tr = evaluate(model, "train")
        f1_va = evaluate(model, "val")
        history.append({"epoch": ep, "loss": loss, "train_f1": f1_tr, "val_f1": f1_va})
        print(f"Epoch {ep}: loss={loss:.3f} train_f1={f1_tr:.3f} val_f1={f1_va:.3f}")
        if f1_va > best_val:
            best_val = f1_va
            torch.save(model.state_dict(), ART_DIR/"ner_bilstm_crf.pt")

    # final test using best weights
    model.load_state_dict(torch.load(ART_DIR/"ner_bilstm_crf.pt"))
    f1_tr = evaluate(model, "train")
    f1_va = evaluate(model, "val")
    f1_te = evaluate(model, "test")
    metrics = {"train_micro_f1": f1_tr, "val_micro_f1": f1_va, "test_micro_f1": f1_te}
    (ART_DIR/"metrics.json").write_text(json.dumps(metrics, indent=2))
    # also save training curve
    Path(ART_DIR/"training_history.json").write_text(json.dumps(history, indent=2))
    print("NER baseline:", metrics)

if __name__ == "__main__":
    main()
