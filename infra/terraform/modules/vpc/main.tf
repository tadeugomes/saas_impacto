variable "name" {}
variable "region" {}
variable "project_id" {}

resource "google_compute_network" "this" {
  name                    = var.name
  auto_create_subnetworks = false
  project                 = var.project_id
}

resource "google_compute_subnetwork" "this" {
  name          = "${var.name}-subnet"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.this.id
  project       = var.project_id
}

resource "google_compute_router" "this" {
  name    = "${var.name}-router"
  region  = var.region
  network = google_compute_network.this.name
}

output "vpc_id" {
  value = google_compute_network.this.id
}

output "vpc_self_link" {
  value = google_compute_network.this.self_link
}

output "subnet_name" {
  value = google_compute_subnetwork.this.name
}
