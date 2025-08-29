# bin/scaffold.sh
#!/usr/bin/env bash
set -euo pipefail

mkdir -p infra/terraform
mkdir -p {pipelines,src,serving,monitoring,tests,notebooks,data/{raw,processed},.github/workflows}
touch DATA_LICENSES.md DATA_README.md README.md

# sensible .gitignore
cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
.venv/
# Notebooks
.ipynb_checkpoints/
# Terraform
*.tfstate
*.tfstate.*
.terraform/
crash.log
# Mac/OS
.DS_Store
# Node
node_modules/
# Logs
*.log
EOF

cat > README.md <<'EOF'
# Intent OPS (MLOps)

This repo houses infra, pipelines, serving, monitoring, tests, and notebooks.
Region: us-east-1 (override via TF var if needed).

Step 1 assets live in infra/terraform; run the Makefile targets below to plan.
EOF
chmod +x bin/scaffold.sh