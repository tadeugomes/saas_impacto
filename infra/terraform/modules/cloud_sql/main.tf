variable "name" {
  type        = string
  description = "Nome da instância Cloud SQL."
}

variable "region" {
  type        = string
  description = "Região da instância."
}

variable "database_version" {
  type        = string
  default     = "POSTGRES_16"
  description = "Versão do PostgreSQL."
}

variable "database_name" {
  type        = string
  description = "Nome do banco operacional."
}

variable "database_user" {
  type        = string
  description = "Usuário administrador do banco."
}

variable "database_password" {
  type        = string
  sensitive   = true
  description = "Senha do usuário do banco."
}

variable "tier" {
  type        = string
  default     = "db-f1-micro"
  description = "Máquina do Cloud SQL."
}

variable "vpc_self_link" {
  type        = string
  default     = null
  description = "VPC privada utilizada para conexão privada."
}

resource "google_sql_database_instance" "this" {
  name             = var.name
  database_version = var.database_version
  region           = var.region

  settings {
    tier = var.tier

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.vpc_self_link
    }
  }
}

resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.this.name
}

resource "google_sql_user" "user" {
  name     = var.database_user
  instance = google_sql_database_instance.this.name
  password = var.database_password
}
