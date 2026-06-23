variable "project_name" {
  description = "Project name used for cluster naming"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID from the VPC module"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs where worker nodes will run"
  type        = list(string)
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
