terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  labels = {
    project     = "ai-code-tester"
    cell        = var.cell_id
    environment = var.environment
  }
}

# ── GKE Cluster ───────────────────────────────────────────────────────────────
resource "google_container_cluster" "gke" {
  name     = "ait-${var.cell_id}"
  location = var.region

  remove_default_node_pool = true
  initial_node_count       = 1

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  resource_labels = local.labels
}

resource "google_container_node_pool" "general" {
  name     = "general"
  cluster  = google_container_cluster.gke.name
  location = var.region

  node_count = var.gke_node_count

  node_config {
    machine_type = var.gke_machine_type
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = local.labels
  }
}

resource "google_container_node_pool" "gpu" {
  name     = "gpu"
  cluster  = google_container_cluster.gke.name
  location = var.region

  initial_node_count = 0

  autoscaling {
    min_node_count = 0
    max_node_count = 2
  }

  node_config {
    machine_type = "n1-standard-4"
    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1
    }
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    labels       = merge(local.labels, { workload = "gpu" })
    taint {
      key    = "nvidia.com/gpu"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
  }
}

# ── Artifact Registry ─────────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "ait" {
  repository_id = "ait"
  format        = "DOCKER"
  location      = var.region
  labels        = local.labels
}

# ── Firestore ─────────────────────────────────────────────────────────────────
resource "google_firestore_database" "db" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# ── Cloud Storage (CDN assets) ────────────────────────────────────────────────
resource "google_storage_bucket" "assets" {
  name          = "ait-${var.cell_id}-assets"
  location      = var.region
  force_destroy = true
  labels        = local.labels

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }
}
