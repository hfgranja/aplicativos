variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "cell_id" {
  description = "Unique cell identifier"
  type        = string
}

variable "environment" {
  type    = string
  default = "production"
}

variable "gke_node_count" {
  type    = number
  default = 3
}

variable "gke_machine_type" {
  type    = string
  default = "n2-standard-2"
}
