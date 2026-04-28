# ── Ollama Compute Engine VM ─────────────────────────────────────────────────
# Runs the Ollama model server inside the VPC.
# Cloud Run services reach it via internal IP (no public internet).
# Startup script installs Ollama and pre-pulls the configured models.

resource "google_compute_instance" "ollama" {
  name         = "${var.app_name}-ollama"
  machine_type = var.ollama_machine_type
  zone         = "${var.region}-b"

  tags = ["ollama-server", "allow-internal"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 60   # GB — models need space (llama3.2 ≈ 4 GB, nomic-embed-text ≈ 300 MB)
      type  = "pd-ssd"
    }
  }

  network_interface {
    network    = google_compute_network.main.name
    subnetwork = google_compute_subnetwork.main.name
    # No access_config = no external IP (internal only)
  }

  service_account {
    email  = google_service_account.cloud_run.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    startup-script = <<-SCRIPT
      #!/bin/bash
      set -e

      # Install Ollama
      if ! command -v ollama &>/dev/null; then
        curl -fsSL https://ollama.com/install.sh | sh
      fi

      # Configure Ollama to listen on all interfaces (VPC-internal only)
      mkdir -p /etc/systemd/system/ollama.service.d
      cat > /etc/systemd/system/ollama.service.d/override.conf <<EOF
      [Service]
      Environment="OLLAMA_HOST=0.0.0.0:11434"
      Environment="OLLAMA_MODELS=/var/lib/ollama/models"
      EOF

      systemctl daemon-reload
      systemctl enable ollama
      systemctl restart ollama

      # Wait for Ollama to be ready
      for i in $(seq 1 30); do
        curl -sf http://localhost:11434/ && break
        sleep 3
      done

      # Pull models (runs in background to not block startup)
      ollama pull ${var.ollama_model}      &
      ollama pull ${var.ollama_embedding_model} &
      wait

      echo "Ollama ready with models ${var.ollama_model} and ${var.ollama_embedding_model}"
    SCRIPT
  }

  allow_stopping_for_update = true

  depends_on = [
    google_project_service.apis,
    google_compute_subnetwork.main,
  ]
}

# Firewall: allow Cloud Run (via VPC connector) to reach Ollama on port 11434
resource "google_compute_firewall" "allow_ollama_internal" {
  name    = "${var.app_name}-allow-ollama"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["11434"]
  }

  source_tags = ["vpc-connector"]
  target_tags = ["ollama-server"]

  description = "Allow Cloud Run VPC connector to reach Ollama server"
}

# Firewall: allow SSH from IAP (for maintenance)
resource "google_compute_firewall" "allow_ssh_iap" {
  name    = "${var.app_name}-allow-ssh-iap"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  # Google IAP source range
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["ollama-server"]
}
