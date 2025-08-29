# variables.tf
variable "project" {
  description = "Project prefix for resource names"
  type        = string
  default     = "intent-ops"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

locals {
  bucket_suffix = "${data.aws_caller_identity.current.account_id}-${var.region}"
  tags = {
    Project     = var.project
    Environment = "staging"
    Owner       = "lok" # change if needed
  }
}
