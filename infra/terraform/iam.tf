# --- SageMaker execution role (used by training/inference jobs) ---
data "aws_iam_policy_document" "sagemaker_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sagemaker_exec" {
  name               = "${local.project}-sagemaker-exec"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume.json
  tags               = local.common_tags
}

# S3, Logs, ECR pull minimal
data "aws_iam_policy_document" "sagemaker_inline" {
  statement {
    sid     = "S3Access"
    actions = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [
      aws_s3_bucket.raw.arn,
      "${aws_s3_bucket.raw.arn}/*",
      aws_s3_bucket.artifacts.arn,
      "${aws_s3_bucket.artifacts.arn}/*",
      aws_s3_bucket.capture.arn,
      "${aws_s3_bucket.capture.arn}/*"
    ]
  }

  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"]
    resources = ["*"]
  }

  statement {
    sid       = "ECRPull"
    actions   = ["ecr:GetAuthorizationToken", "ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage"]
    resources = ["*"]
  }

  # Optional: put CloudWatch metrics
  statement {
    sid       = "CWPutMetrics"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "sagemaker_policy" {
  name        = "${local.project}-sagemaker-inline"
  description = "Least-priv S3/Logs/ECR for SageMaker jobs"
  policy      = data.aws_iam_policy_document.sagemaker_inline.json
}

resource "aws_iam_role_policy_attachment" "sagemaker_attach" {
  role       = aws_iam_role.sagemaker_exec.name
  policy_arn = aws_iam_policy.sagemaker_policy.arn
}

# --- CodeBuild role ---
data "aws_iam_policy_document" "codebuild_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["codebuild.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codebuild" {
  name               = "${local.project}-codebuild"
  assume_role_policy = data.aws_iam_policy_document.codebuild_assume.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "codebuild_inline" {
  statement {
    sid     = "S3Artifacts"
    actions = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [
      aws_s3_bucket.artifacts.arn,
      "${aws_s3_bucket.artifacts.arn}/*"
    ]
  }

  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"]
    resources = ["*"]
  }

  statement {
    sid       = "ECR"
    actions   = ["ecr:GetAuthorizationToken", "ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage", "ecr:PutImage", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart", "ecr:CompleteLayerUpload", "ecr:DescribeRepositories", "ecr:CreateRepository"]
    resources = ["*"]
  }

  statement {
    sid       = "SageMakerMinimal"
    actions   = ["sagemaker:ListModels", "sagemaker:ListModelPackages", "sagemaker:CreateModel", "sagemaker:DescribeModel"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "codebuild_policy" {
  name        = "${local.project}-codebuild-inline"
  description = "CodeBuild S3/Logs/ECR minimal"
  policy      = data.aws_iam_policy_document.codebuild_inline.json
}

resource "aws_iam_role_policy_attachment" "codebuild_attach" {
  role       = aws_iam_role.codebuild.name
  policy_arn = aws_iam_policy.codebuild_policy.arn
}

# --- CodePipeline role ---
data "aws_iam_policy_document" "codepipeline_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["codepipeline.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codepipeline" {
  name               = "${local.project}-codepipeline"
  assume_role_policy = data.aws_iam_policy_document.codepipeline_assume.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "codepipeline_inline" {
  statement {
    sid     = "S3Artifacts"
    actions = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [
      aws_s3_bucket.artifacts.arn,
      "${aws_s3_bucket.artifacts.arn}/*"
    ]
  }

  statement {
    sid       = "StartBuilds"
    actions   = ["codebuild:StartBuild", "codebuild:BatchGetBuilds"]
    resources = ["*"]
  }

  statement {
    sid       = "PassRoleToCodeBuild"
    actions   = ["iam:PassRole"]
    resources = [aws_iam_role.codebuild.arn]
  }

  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "codepipeline_policy" {
  name        = "${local.project}-codepipeline-inline"
  description = "CodePipeline minimal to coordinate CodeBuild & S3"
  policy      = data.aws_iam_policy_document.codepipeline_inline.json
}

resource "aws_iam_role_policy_attachment" "codepipeline_attach" {
  role       = aws_iam_role.codepipeline.name
  policy_arn = aws_iam_policy.codepipeline_policy.arn
}
