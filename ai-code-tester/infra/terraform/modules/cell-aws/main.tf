terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

locals {
  tags = {
    Project     = "ai-code-tester"
    Cell        = var.cell_id
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── VPC ───────────────────────────────────────────────────────────────────────
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "ait-${var.cell_id}"
  cidr = "10.0.0.0/16"

  azs             = ["${var.region}a", "${var.region}b", "${var.region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = false

  tags = local.tags
}

# ── EKS Cluster ───────────────────────────────────────────────────────────────
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "ait-${var.cell_id}"
  cluster_version = "1.30"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      instance_types = [var.eks_node_instance_type]
      min_size       = 2
      max_size       = 6
      desired_size   = var.eks_node_count
    }
    gpu = {
      instance_types = ["g4dn.xlarge"]
      min_size       = 0
      max_size       = 2
      desired_size   = 0
      labels = { "workload" = "gpu" }
      taints = [{ key = "nvidia.com/gpu", value = "true", effect = "NO_SCHEDULE" }]
    }
  }

  tags = local.tags
}

# ── ECR Repositories ──────────────────────────────────────────────────────────
locals {
  services = ["analysis-service", "advisory-service", "git-proxy", "storage-service", "cell-health", "frontend"]
}

resource "aws_ecr_repository" "services" {
  for_each = toset(local.services)

  name                 = "ait/${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.tags
}

# ── DynamoDB Tables ───────────────────────────────────────────────────────────
resource "aws_dynamodb_table" "analyses" {
  name         = var.dynamodb_table_analyses
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }
  attribute {
    name = "sk"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "incidents" {
  name         = var.dynamodb_table_incidents
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }
  attribute {
    name = "sk"
    type = "S"
  }

  tags = local.tags
}

# ── CloudFront + S3 (static assets fallback) ─────────────────────────────────
resource "aws_s3_bucket" "assets" {
  bucket = "ait-${var.cell_id}-assets"
  tags   = local.tags
}

resource "aws_cloudfront_distribution" "cdn" {
  enabled             = true
  default_root_object = "index.html"

  origin {
    domain_name = aws_s3_bucket.assets.bucket_regional_domain_name
    origin_id   = "s3-assets"
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3-assets"
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = local.tags
}
