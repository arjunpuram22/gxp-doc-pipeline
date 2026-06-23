variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC - defines the IP address range"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of AWS availability zones to deploy subnets into"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets - EKS nodes live here"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets - load balancers live here"
  type        = list(string)
}

variable "tags" {
  description = "Common tags applied to all resources for tracking"
  type        = map(string)
  default     = {}
}
