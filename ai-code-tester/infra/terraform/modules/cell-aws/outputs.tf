output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "ecr_registry" {
  value = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com"
}

output "dynamodb_table_analyses" {
  value = aws_dynamodb_table.analyses.name
}

output "cloudfront_domain" {
  value = aws_cloudfront_distribution.cdn.domain_name
}

data "aws_caller_identity" "current" {}
