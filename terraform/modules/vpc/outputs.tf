output "vpc_id" {
  description = "ID of the VPC - used by EKS module to know which network to join"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of private subnets - EKS worker nodes deploy here"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "IDs of public subnets - load balancers deploy here"
  value       = module.vpc.public_subnets
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC - used for security group rules"
  value       = module.vpc.vpc_cidr_block
}
