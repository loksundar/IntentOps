locals {
  project = var.project
  region  = var.aws_region
  account = data.aws_caller_identity.current.account_id

  # Globally unique suffix for S3
  bucket_suffix = "${local.account}-${local.region}"

  # Bucket names
  raw_bucket       = "${local.project}-raw-${local.bucket_suffix}"
  artifacts_bucket = "${local.project}-artifacts-${local.bucket_suffix}"
  capture_bucket   = "${local.project}-capture-${local.bucket_suffix}"

  common_tags = {
    Project     = local.project
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
