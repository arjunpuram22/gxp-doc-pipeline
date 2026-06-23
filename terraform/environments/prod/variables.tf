variable "project_name" {
  description = "Project name"
  type        = string
  default     = "gxp-doc-pipeline"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {
    project     = "gxp-doc-pipeline"
    environment = "prod"
    managed_by  = "terraform"
    compliance  = "gxp"
  }
}
