resource "aws_s3_bucket" "raw" {
  bucket = local.raw_bucket
  tags   = local.common_tags
}

resource "aws_s3_bucket" "artifacts" {
  bucket = local.artifacts_bucket
  tags   = local.common_tags
}

resource "aws_s3_bucket" "capture" {
  bucket = local.capture_bucket
  tags   = local.common_tags
}

# Block public access for all
resource "aws_s3_bucket_public_access_block" "raw" {
  bucket                  = aws_s3_bucket.raw.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "capture" {
  bucket                  = aws_s3_bucket.capture.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning
resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration { status = var.enable_bucket_versioning ? "Enabled" : "Suspended" }
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration { status = var.enable_bucket_versioning ? "Enabled" : "Suspended" }
}

resource "aws_s3_bucket_versioning" "capture" {
  bucket = aws_s3_bucket.capture.id
  versioning_configuration { status = var.enable_bucket_versioning ? "Enabled" : "Suspended" }
}

# Default encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "capture" {
  bucket = aws_s3_bucket.capture.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle for capture bucket (keep it lean)
resource "aws_s3_bucket_lifecycle_configuration" "capture" {
  bucket = aws_s3_bucket.capture.id
  rule {
    id     = "expire-capture"
    status = "Enabled"
    filter {}
    expiration { days = var.capture_retention_days }
    noncurrent_version_expiration { noncurrent_days = var.capture_retention_days }
  }
}
