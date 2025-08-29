# outputs.tf
output "bucket_raw" { value = aws_s3_bucket.raw.bucket }
output "bucket_artifacts" { value = aws_s3_bucket.artifacts.bucket }
output "bucket_capture" { value = aws_s3_bucket.capture.bucket }

output "sagemaker_execution_role_arn" { value = aws_iam_role.sagemaker_execution.arn }
output "codebuild_role_arn" { value = aws_iam_role.codebuild_role.arn }
output "codepipeline_role_arn" { value = aws_iam_role.codepipeline_role.arn }
