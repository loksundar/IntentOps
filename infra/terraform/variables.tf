variable "project" {
  description = "Project slug used in names"
  type        = string
  default     = "intent-ops"
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "enable_bucket_versioning" {
  description = "Enable S3 versioning for buckets"
  type        = bool
  default     = true
}

variable "capture_retention_days" {
  description = "How long to keep data-capture objects"
  type        = number
  default     = 30
}
