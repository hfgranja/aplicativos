module "cell" {
  source = "../../modules/cell-gcp"

  project_id       = var.gcp_project_id
  region           = "us-central1"
  cell_id          = "gcp-us-central1"
  environment      = "production"
  gke_node_count   = 3
  gke_machine_type = "n2-standard-2"
}

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

terraform {
  backend "gcs" {
    bucket = "ait-terraform-state"
    prefix = "cells/gcp-us-central1"
  }
}
