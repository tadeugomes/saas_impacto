variable "name" {}
variable "region" {}
variable "image" {}
variable "service_account_email" {}
variable "container_port" { default = 8000 }
variable "memory" { default = "1Gi" }
variable "cpu" { default = "1000m" }
variable "min_instances" { default = 0 }
variable "max_instances" { default = 1 }
variable "env_vars" { type = map(string) }
variable "ingress" { default = "INGRESS_TRAFFIC_ALL" }

resource "google_cloud_run_v2_service" "this" {
  name     = var.name
  location = var.region

  template {
    service_account = var.service_account_email
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    containers {
      image = var.image
      ports {
        container_port = var.container_port
      }
      resources {
        limits = {
          memory = var.memory
          cpu    = var.cpu
        }
      }
      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }
  ingress = var.ingress
}

resource "google_cloud_run_v2_service_iam_member" "invoker" {
  count    = var.service_account_email == "" ? 0 : 1
  location = var.region
  name     = google_cloud_run_v2_service.this.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.service_account_email}"
}
