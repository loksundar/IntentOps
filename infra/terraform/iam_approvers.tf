########################################
# Approver Users + Least-Priv Group
########################################

# Group for model/pipeline approvals; MFA enforced
resource "aws_iam_group" "approvers" {
  name = "${local.project}-approvers"
  #tags = local.common_tags
}

# Deny anything if MFA is not present (console/API), except iam:*Self* so they can set MFA/password
data "aws_iam_policy_document" "deny_without_mfa" {
  statement {
    sid       = "DenyAllIfNoMFA"
    effect    = "Deny"
    actions   = ["*"]
    resources = ["*"]
    condition {
      test     = "BoolIfExists"
      variable = "aws:MultiFactorAuthPresent"
      values   = ["false"]
    }
  }

  # Allow list of self-management actions even without MFA so the user can set it up
  statement {
    sid    = "AllowListSelf"
    effect = "Allow"
    actions = [
      "iam:GetUser",
      "iam:ListMFADevices",
      "iam:ListVirtualMFADevices",
      "iam:CreateVirtualMFADevice",
      "iam:EnableMFADevice",
      "iam:ResyncMFADevice",
      "iam:DeactivateMFADevice",
      "iam:ListAccessKeys",
      "iam:CreateAccessKey",
      "iam:DeleteAccessKey",
      "iam:GetLoginProfile",
      "iam:CreateLoginProfile",
      "iam:UpdateLoginProfile",
      "iam:ChangePassword"
    ]
    resources = ["arn:aws:iam::*:user/${aws_iam_user.ml_lead.name}", "arn:aws:iam::*:user/${aws_iam_user.product_owner.name}"]
  }
}

resource "aws_iam_policy" "deny_without_mfa" {
  name        = "${local.project}-deny-without-mfa"
  description = "Deny all actions unless MFA is present; allow self-management"
  policy      = data.aws_iam_policy_document.deny_without_mfa.json
}

# Approvals for SageMaker Model Registry (update approval status) and read-only describe/list
data "aws_iam_policy_document" "model_registry_approvals" {
  statement {
    sid = "SageMakerModelRegistryApprovals"
    actions = [
      "sagemaker:UpdateModelPackage",
      "sagemaker:DescribeModelPackage",
      "sagemaker:ListModelPackages",
      "sagemaker:DescribeModelPackageGroup",
      "sagemaker:ListModelPackageGroups"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "model_registry_approvals" {
  name        = "${local.project}-model-registry-approvals"
  description = "Allow approvers to approve/describe model packages in SageMaker Model Registry"
  policy      = data.aws_iam_policy_document.model_registry_approvals.json
}

# Approvals for CodePipeline Manual approval actions + read state
data "aws_iam_policy_document" "codepipeline_approvals" {
  statement {
    sid = "PipelineApprovals"
    actions = [
      "codepipeline:PutApprovalResult",
      "codepipeline:GetPipelineState",
      "codepipeline:ListPipelines",
      "codepipeline:ListPipelineExecutions"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "codepipeline_approvals" {
  name        = "${local.project}-codepipeline-approvals"
  description = "Allow approvers to approve CodePipeline manual gates and read pipeline state"
  policy      = data.aws_iam_policy_document.codepipeline_approvals.json
}

# Attach policies to the approvers group
resource "aws_iam_group_policy_attachment" "approvers_mfa" {
  group      = aws_iam_group.approvers.name
  policy_arn = aws_iam_policy.deny_without_mfa.arn
}

resource "aws_iam_group_policy_attachment" "approvers_registry" {
  group      = aws_iam_group.approvers.name
  policy_arn = aws_iam_policy.model_registry_approvals.arn
}

resource "aws_iam_group_policy_attachment" "approvers_pipeline" {
  group      = aws_iam_group.approvers.name
  policy_arn = aws_iam_policy.codepipeline_approvals.arn
}

# IAM Users
resource "aws_iam_user" "ml_lead" {
  name = "ml-lead"
  tags = merge(local.common_tags, { Role = "MLLead" })
}

resource "aws_iam_user" "product_owner" {
  name = "product-owner"
  tags = merge(local.common_tags, { Role = "ProductOwner" })
}

# Put both users in the approvers group
resource "aws_iam_user_group_membership" "ml_lead_groups" {
  user   = aws_iam_user.ml_lead.name
  groups = [aws_iam_group.approvers.name]
}

resource "aws_iam_user_group_membership" "product_owner_groups" {
  user   = aws_iam_user.product_owner.name
  groups = [aws_iam_group.approvers.name]
}

output "approver_users" {
  value = {
    ml_lead       = aws_iam_user.ml_lead.name
    product_owner = aws_iam_user.product_owner.name
    group         = aws_iam_group.approvers.name
  }
}
