# iam.tf
# SageMaker execution role (assumed by SageMaker jobs/endpoints)
resource "aws_iam_role" "sagemaker_execution" {
  name = "${var.project}-sagemaker-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "sagemaker.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
  tags = local.tags
}

# Limit S3 to our three buckets; allow common SM/ECR/Logs actions needed later
resource "aws_iam_policy" "sagemaker_policy" {
  name = "${var.project}-sagemaker-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "S3AccessBuckets"
        Effect = "Allow",
        Action = ["s3:ListBucket"],
        Resource = [
          aws_s3_bucket.raw.arn,
          aws_s3_bucket.artifacts.arn,
          aws_s3_bucket.capture.arn
        ]
      },
      {
        Sid    = "S3ObjectsRW"
        Effect = "Allow",
        Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload", "s3:ListBucketMultipartUploads"],
        Resource = [
          "${aws_s3_bucket.raw.arn}/*",
          "${aws_s3_bucket.artifacts.arn}/*",
          "${aws_s3_bucket.capture.arn}/*"
        ]
      },
      {
        Sid      = "Logs"
        Effect   = "Allow",
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"],
        Resource = "*"
      },
      {
        Sid      = "ECRPull"
        Effect   = "Allow",
        Action   = ["ecr:GetAuthorizationToken", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer", "ecr:BatchCheckLayerAvailability"],
        Resource = "*"
      },
      {
        Sid    = "SageMakerCore"
        Effect = "Allow",
        Action = [
          "sagemaker:CreateTrainingJob", "sagemaker:CreateProcessingJob", "sagemaker:CreateTransformJob",
          "sagemaker:CreateModel", "sagemaker:CreateEndpointConfig", "sagemaker:CreateEndpoint", "sagemaker:UpdateEndpoint",
          "sagemaker:InvokeEndpoint", "sagemaker:Describe*", "sagemaker:List*", "sagemaker:DeleteModel", "sagemaker:DeleteEndpoint", "sagemaker:DeleteEndpointConfig"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_sm" {
  role       = aws_iam_role.sagemaker_execution.name
  policy_arn = aws_iam_policy.sagemaker_policy.arn
}

# CodeBuild service role
resource "aws_iam_role" "codebuild_role" {
  name = "${var.project}-codebuild-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "codebuild.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
  tags = local.tags
}

resource "aws_iam_policy" "codebuild_policy" {
  name = "${var.project}-codebuild-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid      = "Logs",
        Effect   = "Allow",
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Resource = "*"
      },
      {
        Sid    = "S3Artifacts",
        Effect = "Allow",
        Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
        Resource = [
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      },
      {
        Sid      = "ECRPull",
        Effect   = "Allow",
        Action   = ["ecr:GetAuthorizationToken", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer", "ecr:BatchCheckLayerAvailability"],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_cb" {
  role       = aws_iam_role.codebuild_role.name
  policy_arn = aws_iam_policy.codebuild_policy.arn
}

# CodePipeline service role (to orchestrate builds using the artifacts bucket)
resource "aws_iam_role" "codepipeline_role" {
  name = "${var.project}-codepipeline-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "codepipeline.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
  tags = local.tags
}

resource "aws_iam_policy" "codepipeline_policy" {
  name = "${var.project}-codepipeline-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "S3Artifacts",
        Effect = "Allow",
        Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
        Resource = [
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      },
      {
        Sid      = "StartBuilds",
        Effect   = "Allow",
        Action   = ["codebuild:StartBuild", "codebuild:BatchGetBuilds"],
        Resource = "*"
      },
      {
        Sid      = "PassCodeBuildRole",
        Effect   = "Allow",
        Action   = ["iam:PassRole"],
        Resource = aws_iam_role.codebuild_role.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_cp" {
  role       = aws_iam_role.codepipeline_role.name
  policy_arn = aws_iam_policy.codepipeline_policy.arn
}
