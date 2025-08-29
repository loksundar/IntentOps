AWS_PROFILE ?= default
REGION ?= us-east-2

.PHONY: scaffold tf-init tf-plan tf-apply record-plan

scaffold:
	bash bin\scaffold.sh
	@echo "Scaffold complete."

tf-init:
	cd infra/terraform && terraform init

tf-plan:
	cd infra/terraform && terraform fmt -recursive && terraform validate && terraform plan -out plan.out -var="region=$(REGION)"

tf-apply:
	cd infra/terraform && terraform apply plan.out


record-plan:
	cd infra/terraform && terraform show -no-color plan.out > plan.txt
	- git rev-parse HEAD > infra/terraform/PLAN_COMMIT.txt || echo UNCOMMITTED > infra/terraform/PLAN_COMMIT.txt
	@echo "Plan recorded to infra/terraform/plan.txt and commit captured in PLAN_COMMIT.txt"
