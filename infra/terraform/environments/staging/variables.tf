variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "region" {
  type        = string
  description = "GCP region"
  default     = "us-east1"
}

variable "env_prefix" {
  type        = string
  description = "Prefixo de ambiente"
  default     = "staging"
}

variable "database_password" {
  type      = string
  sensitive = true
}

variable "api_image" {
  type        = string
  description = "Imagem Docker do serviço API"
}

variable "worker_image" {
  type        = string
  description = "Imagem Docker do worker Celery"
}

variable "secrets" {
  type        = map(string)
  description = "Mapa de segredos (nome -> valor)"
  default     = {}
}
