variable "name" {
  type        = string
  description = "Nome base da rede."
}

variable "region" {
  type        = string
  description = "Região da VPC."
}

variable "project_id" {
  type        = string
  description = "ID do projeto GCP."
}

variable "subnet_cidr" {
  type        = string
  default     = "10.0.0.0/20"
  description = "CIDR da subnet principal."
}

variable "connector_cidr" {
  type        = string
  default     = "10.8.0.0/28"
  description = "CIDR usada pelo Cloud Run connector."
}

variable "enable_nat" {
  type        = bool
  default     = true
  description = "Cria Cloud NAT para saída da VPC."
}

variable "enable_cloud_sql_peering" {
  type        = bool
  default     = true
  description = "Reserva faixa e cria peering para instâncias Cloud SQL privadas."
}

resource "google_compute_network" "this" {
  name                    = var.name
  auto_create_subnetworks = false
  project                 = var.project_id
}

resource "google_compute_subnetwork" "this" {
  name          = "${var.name}-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.this.id
  project       = var.project_id
}

resource "google_compute_router" "this" {
  name    = "${var.name}-router"
  region  = var.region
  network = google_compute_network.this.self_link
}

resource "google_compute_router_nat" "this" {
  count = var.enable_nat ? 1 : 0

  name                               = "${var.name}-nat"
  router                             = google_compute_router.this.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat  = ["ALL_SUBNETWORKS_ALL_IP_RANGES"]
  depends_on = [
    google_compute_router.this,
  ]

  dynamic "log_config" {
    for_each = var.enable_nat ? [1] : []
    content {
      enable = true
      filter = "ERRORS_ONLY"
    }
  }
}

resource "google_compute_global_address" "private_service_access_range" {
  count        = var.enable_cloud_sql_peering ? 1 : 0
  project      = var.project_id
  name         = "${var.name}-private-range"
  purpose      = "VPC_PEERING"
  address_type = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.this.self_link
}

resource "google_service_networking_connection" "private_vpc_connection" {
  count = var.enable_cloud_sql_peering ? 1 : 0

  network                 = google_compute_network.this.self_link
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_access_range[0].name]
}

resource "google_vpc_access_connector" "run_connector" {
  name         = "${var.name}-connector"
  project      = var.project_id
  region       = var.region
  network      = google_compute_network.this.name
  ip_cidr_range = var.connector_cidr
  min_instances = 2
  max_instances = 10
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

output "connector_id" {
  value = google_vpc_access_connector.run_connector.id
}

output "connector_name" {
  value = google_vpc_access_connector.run_connector.name
}

output "connector_full_name" {
  value = google_vpc_access_connector.run_connector.self_link
}
