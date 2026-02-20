variable "name" {
  type        = string
  description = "Nome da instância Memorystore."
}

variable "region" {
  type        = string
  description = "Região da instância."
}

variable "memory_size_gb" {
  type        = number
  default     = 1
  description = "Tamanho da memória em GB."
}

variable "tier" {
  type        = string
  default     = "BASIC"
  description = "Tier do Redis (BASIC ou STANDARD_HA)."
}

variable "vpc_connect_mode" {
  type        = string
  default     = "PRIVATE_SERVICE_ACCESS"
  description = "Modo de conectividade (private service access)."
}

resource "google_redis_instance" "this" {
  name           = var.name
  tier           = var.tier
  memory_size_gb = var.memory_size_gb
  region         = var.region
  connect_mode   = var.vpc_connect_mode
}

output "host" {
  value = google_redis_instance.this.host
}

output "port" {
  value = google_redis_instance.this.port
}
