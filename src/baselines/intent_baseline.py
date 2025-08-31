# src/baselines/intent_baseline.py
import json, random
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score
from sklearn.utils import shuffle as sk_shuffle
import joblib
import matplotlib.pyplot as plt

SEED = 42
random.seed(SEED); np.random.seed(SEED)

DATA_DIR = Path("data/processed/banking77")
ART_DIR  = Path("artifacts/baselines/intent"); ART_DIR.mkdir(parents=True, exist_ok=True)

def load_banking77():
    tr = pd.read_csv(DATA_DIR/"train.csv")
    va = pd.read_csv(DATA_DIR/"val.csv")
    te = pd.read_csv(DATA_DIR/"test.csv")
    return tr, va, te

def plot_confusion(y_true, y_pred, labels, out_png, max_labels=30):
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(labels))))
    np.savetxt(out_png.replace(".png",".csv"), cm, fmt="%d", delimiter=",")
    k = min(max_labels, len(labels))
    fig = plt.figure(figsize=(8,6))
    plt.imshow(cm[:k,:k], interpolation="nearest")
    plt.title(f"Confusion (top {k} labels)"); plt.colorbar()
    plt.xlabel("pred"); plt.ylabel("true")
    plt.tight_layout(); plt.savefig(out_png, dpi=150); plt.close(fig)

def train_eval_once(tr, va, vec_params, C):
    vec = TfidfVectorizer(**vec_params).fit(tr["text_norm"].tolist())
    Xtr, Xva = vec.transform(tr["text_norm"]), vec.transform(va["text_norm"])
    ytr, yva = tr["intent_id"].to_numpy(), va["intent_id"].to_numpy()
    clf = LogisticRegression(C=C, max_iter=2000, n_jobs=-1, solver="lbfgs", multi_class="auto")
    clf.fit(Xtr, ytr)
    yp_tr = clf.predict(Xtr); yp_va = clf.predict(Xva)
    acc_tr = accuracy_score(ytr, yp_tr)
    acc_va = accuracy_score(yva, yp_va)
    gap = acc_tr - acc_va
    return {"acc_tr":acc_tr, "acc_va":acc_va, "gap":gap}, vec, clf

def select_model(tr, va):
    # small grid; fast but effective
    vec_grid = [
        {"ngram_range": (1,1), "min_df":2, "max_df":0.90, "sublinear_tf":True, "strip_accents":"unicode"},
        {"ngram_range": (1,1), "min_df":2, "max_df":0.95, "sublinear_tf":True, "strip_accents":"unicode"},
        {"ngram_range": (1,2), "min_df":2, "max_df":0.90, "sublinear_tf":True, "strip_accents":"unicode"},
        {"ngram_range": (1,2), "min_df":2, "max_df":0.95, "sublinear_tf":True, "strip_accents":"unicode"},
    ]
    C_grid = [0.25, 0.5, 1.0]

    best = None
    best_score = -1e9
    for vp in vec_grid:
        for C in C_grid:
            m, vec, clf = train_eval_once(tr, va, vp, C)
            # penalize overfitting beyond 5pp gap
            score = m["acc_va"] - 0.6 * max(0.0, m["gap"] - 0.05)
            if score > best_score:
                best_score = score
                best = {"vec_params": vp, "C": C, "metrics": m, "vec": vec, "clf": clf}
            print(f"try vec={vp['ngram_range']} max_df={vp['max_df']} C={C} "
                  f"-> val={m['acc_va']:.4f} gap={m['gap']:.4f} score={score:.4f}")
    return best

def finalize_and_save(best, tr, va, te):
    vec, clf = best["vec"], best["clf"]
    labels = json.load(open("data/processed/label_maps/intent_label_map.json"))["labels"]

    # test eval
    Xtr, Xva, Xte = vec.transform(tr["text_norm"]), vec.transform(va["text_norm"]), vec.transform(te["text_norm"])
    ytr, yva, yte = tr["intent_id"].to_numpy(), va["intent_id"].to_numpy(), te["intent_id"].to_numpy()
    acc_tr = accuracy_score(ytr, clf.predict(Xtr))
    acc_va = accuracy_score(yva, clf.predict(Xva))
    yp_te  = clf.predict(Xte); acc_te = accuracy_score(yte, yp_te)

    # plots + saves
    plot_confusion(ytr, clf.predict(Xtr), labels, str(ART_DIR/"confusion_train.png"))
    plot_confusion(yva, clf.predict(Xva), labels, str(ART_DIR/"confusion_val.png"))
    plot_confusion(yte, yp_te,            labels, str(ART_DIR/"confusion_test.png"))
    joblib.dump(vec, ART_DIR/"tfidf.joblib")
    joblib.dump(clf, ART_DIR/"logreg.joblib")
    (ART_DIR/"metrics.json").write_text(json.dumps(
        {"train_acc":acc_tr, "val_acc":acc_va, "test_acc":acc_te}, indent=2))
    (ART_DIR/"selected_params.json").write_text(json.dumps(
        {"vec_params":best["vec_params"], "C":best["C"]}, indent=2))
    print("Intent baseline (selected):", {"train_acc":acc_tr, "val_acc":acc_va, "test_acc":acc_te})

def randomized_label_sanity(tr, va, vec):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    Xtr = vec.transform(tr["text_norm"]); Xva = vec.transform(va["text_norm"])
    ytr = tr["intent_id"].to_numpy()
    ytr_rand = sk_shuffle(ytr, random_state=SEED)
    clf = LogisticRegression(C=0.5, max_iter=1000, n_jobs=-1, solver="lbfgs", multi_class="auto")
    clf.fit(Xtr, ytr_rand)
    acc_rand = accuracy_score(va["intent_id"], clf.predict(Xva))
    (ART_DIR/"sanity.json").write_text(json.dumps({"val_acc_random_labels": acc_rand}, indent=2))
    print("Random-label sanity val acc:", acc_rand)
    return acc_rand

def oos_auroc(vec, clf):
    try:
        oos1 = json.loads(Path("data/raw/clinc_oos/data_oos_plus.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("OOS json not found; skipping AUROC.")
        return None
    oos_texts = []
    for k, v in oos1.items():
        if not str(k).lower().startswith("oos"):
            continue
        for item in v:
            if isinstance(item, list) and len(item) > 0: oos_texts.append(str(item[0]))
            else: oos_texts.append(str(item))
    oos_texts = [t.strip() for t in oos_texts if t and isinstance(t, str)]
    if len(oos_texts) > 2000:
        rng = np.random.default_rng(SEED); oos_texts = list(rng.choice(oos_texts, size=2000, replace=False))
    te = pd.read_csv(DATA_DIR/"test.csv")
    X_ind = vec.transform(te["text_norm"].tolist()); X_oos = vec.transform(oos_texts)
    p_ind = clf.predict_proba(X_ind).max(axis=1); p_oos = clf.predict_proba(X_oos).max(axis=1)
    y_true = np.array([0]*len(p_ind) + [1]*len(p_oos))
    scores = np.concatenate([1 - p_ind, 1 - p_oos])
    auroc = roc_auc_score(y_true, scores)
    (ART_DIR/"oos.json").write_text(json.dumps({"auroc": float(auroc), "n_ind": len(p_ind), "n_oos": len(p_oos)}, indent=2))
    print("OOS AUROC:", auroc); return auroc

if __name__ == "__main__":
    tr, va, te = load_banking77()
    best = select_model(tr, va)
    finalize_and_save(best, tr, va, te)
    # sanity + OOS with the chosen vectorizer
    vec, clf = best["vec"], best["clf"]
    randomized_label_sanity(tr, va, vec)
    oos_auroc(vec, clf)
    print("DONE.")
