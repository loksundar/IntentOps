output "account_id" { value = data.aws_caller_identity.current.account_id }

output "buckets" {
  value = {
    raw       = aws_s3_bucket.raw.bucket
    artifacts = aws_s3_bucket.artifacts.bucket
    capture   = aws_s3_bucket.capture.bucket
  }
}

output "roles" {
  value = {
    sagemaker_execution = aws_iam_role.sagemaker_exec.arn
    codebuild_role      = aws_iam_role.codebuild.arn
    codepipeline_role   = aws_iam_role.codepipeline.arn
  }
}
