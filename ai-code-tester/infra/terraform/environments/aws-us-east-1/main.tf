module "cell" {
  source = "../../modules/cell-aws"

  region      = "us-east-1"
  cell_id     = "aws-us-east-1"
  environment = "production"

  eks_node_instance_type   = "m5.large"
  eks_node_count           = 3
  dynamodb_table_analyses  = "ait-analyses"
  dynamodb_table_incidents = "ait-incidents"
}

terraform {
  backend "s3" {
    bucket = "ait-terraform-state"
    key    = "cells/aws-us-east-1/terraform.tfstate"
    region = "us-east-1"
  }
}
