module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.0.0"

  cluster_name    = var.project_name
  cluster_version = "1.32"

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids

  # Allow kubectl access from your machine
  cluster_endpoint_public_access = true

  # EKS worker nodes - the machines that run your containers
  eks_managed_node_groups = {
    main = {
      min_size       = 1
      max_size       = 3
      desired_size   = 2

      instance_types = ["t3.medium"]

      labels = {
        environment = "prod"
        project     = var.project_name
      }
    }
  }

  tags = var.tags
}
