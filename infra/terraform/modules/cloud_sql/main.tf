variable "name" {}
variable "region" {}
variable "database_version" { default = "POSTGRES_16" }
variable "database_name" {}
variable "database_user" {}
variable "database_password" { sensitive = true }
variable "vpc_self_link" { default = null }

resource "google_sql_database_instance" "this" {
  name             = var.name
  database_version = var.database_version
  region           = var.region

  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled    = true
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
