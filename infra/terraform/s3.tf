# infra/terraform/s3.tf

# ---------- RAW ----------
resource "aws_s3_bucket" "raw" {
  bucket = "${var.project}-raw-${local.bucket_suffix}"
  tags   = local.tags
}

resource "aws_s3_bucket_public_access_block" "raw_block" {
  bucket                  = aws_s3_bucket.raw.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "raw_versioning" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw_sse" {
  bucket = aws_s3_bucket.raw.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ---------- ARTIFACTS ----------
resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.project}-artifacts-${local.bucket_suffix}"
  tags   = local.tags
}

resource "aws_s3_bucket_public_access_block" "artifacts_block" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "artifacts_versioning" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts_sse" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ---------- CAPTURE ----------
resource "aws_s3_bucket" "capture" {
  bucket = "${var.project}-capture-${local.bucket_suffix}"
  tags   = local.tags
}

resource "aws_s3_bucket_public_access_block" "capture_block" {
  bucket                  = aws_s3_bucket.capture.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "capture_versioning" {
  bucket = aws_s3_bucket.capture.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "capture_sse" {
  bucket = aws_s3_bucket.capture.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
