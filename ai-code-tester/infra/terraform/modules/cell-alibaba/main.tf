terraform {
  required_providers {
    alicloud = {
      source  = "aliyun/alicloud"
      version = "~> 1.200"
    }
  }
}

provider "alicloud" {
  region = var.region
}

locals {
  tags = {
    Project     = "ai-code-tester"
    Cell        = var.cell_id
    Environment = var.environment
  }
}

# ── VPC ───────────────────────────────────────────────────────────────────────
resource "alicloud_vpc" "vpc" {
  vpc_name   = "ait-${var.cell_id}"
  cidr_block = "10.0.0.0/16"
  tags       = local.tags
}

resource "alicloud_vswitch" "vsw" {
  count      = 3
  vpc_id     = alicloud_vpc.vpc.id
  cidr_block = "10.0.${count.index + 1}.0/24"
  zone_id    = "${var.region}-${element(["a", "b", "c"], count.index)}"
  tags       = local.tags
}

# ── ACK (Alibaba Container Service for Kubernetes) ────────────────────────────
resource "alicloud_cs_managed_kubernetes" "ack" {
  name                 = "ait-${var.cell_id}"
  cluster_spec         = "ack.pro.small"
  version              = "1.30.0-aliyun.1"
  worker_vswitch_ids   = alicloud_vswitch.vsw[*].id
  pod_cidr             = "172.20.0.0/16"
  service_cidr         = "172.21.0.0/20"
  new_nat_gateway      = true
  worker_instance_type = var.ack_instance_type
  worker_number        = var.ack_node_count
  tags                 = local.tags
}

# ── ACR (Alibaba Container Registry) ─────────────────────────────────────────
resource "alicloud_cr_namespace" "ns" {
  name               = "ait"
  auto_create        = true
  default_visibility = "PRIVATE"
}

locals {
  services = ["analysis-service", "advisory-service", "git-proxy", "storage-service", "cell-health", "frontend"]
}

resource "alicloud_cr_repo" "repos" {
  for_each  = toset(local.services)
  namespace = alicloud_cr_namespace.ns.name
  name      = each.key
  summary   = "AI Code Tester - ${each.key}"
  repo_type = "PRIVATE"
}

# ── Table Store ───────────────────────────────────────────────────────────────
resource "alicloud_ots_instance" "ots" {
  name        = var.tablestore_instance
  description = "AI Code Tester storage for ${var.cell_id}"
  accessed_by = "Any"
  tags        = local.tags
}

resource "alicloud_ots_table" "analyses" {
  instance_name = alicloud_ots_instance.ots.name
  table_name    = "ait_analyses"
  time_to_live  = 7776000 # 90 days

  primary_key {
    name = "id"
    type = "String"
  }

  max_version = 1
}

resource "alicloud_ots_table" "incidents" {
  instance_name = alicloud_ots_instance.ots.name
  table_name    = "ait_incidents"
  time_to_live  = -1

  primary_key {
    name = "id"
    type = "String"
  }

  max_version = 1
}

# ── OSS (Object Storage) ──────────────────────────────────────────────────────
resource "alicloud_oss_bucket" "assets" {
  bucket = "ait-${var.cell_id}-assets"
  acl    = "public-read"
  tags   = local.tags

  website {
    index_document = "index.html"
    error_document = "index.html"
  }
}
