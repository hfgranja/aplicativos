module "cell" {
  source = "../../modules/cell-alibaba"

  region              = "ap-east-1"
  cell_id             = "alibaba-ap-east-1"
  environment         = "production"
  ack_node_count      = 3
  ack_instance_type   = "ecs.c6.xlarge"
  tablestore_instance = "ait-ap-east-1"
}

terraform {
  backend "oss" {
    bucket = "ait-terraform-state"
    prefix = "cells/alibaba-ap-east-1"
    region = "ap-east-1"
  }
}
