variable "name" {
  type        = string
  description = "Nome do serviço Cloud Run."
}

variable "region" {
  type        = string
  description = "Região do recurso Cloud Run."
}

variable "image" {
  type        = string
  description = "Imagem do container."
}

variable "service_account_email" {
  type        = string
  description = "Service account para execução do serviço."
}

variable "container_port" {
  type        = number
  default     = 8000
  description = "Porta de escuta da aplicação."
}

variable "memory" {
  type        = string
  default     = "1Gi"
  description = "Memória alocada para cada instância."
}

variable "cpu" {
  type        = string
  default     = "1000m"
  description = "CPU alocada para cada instância."
}

variable "min_instances" {
  type        = number
  default     = 0
  description = "Número mínimo de instâncias."
}

variable "max_instances" {
  type        = number
  default     = 1
  description = "Número máximo de instâncias."
}

variable "env_vars" {
  type        = map(string)
  default     = {}
  description = "Variáveis de ambiente em texto."
}

variable "secret_env_vars" {
  type        = map(string)
  default     = {}
  description = "Variáveis de ambiente via Secret Manager (map nome -> secret_id)."
}

variable "vpc_connector" {
  type        = string
  default     = ""
  description = "Nome completo do Serverless VPC Access Connector."
}

variable "vpc_egress" {
  type        = string
  default     = "ALL_TRAFFIC"
  description = "Estratégia de egress para o conector VPC."
}

variable "ingress" {
  type        = string
  default     = "INGRESS_TRAFFIC_ALL"
  description = "Política de entrada do serviço."
}

locals {
  safe_env_vars         = var.env_vars
  safe_secret_env_vars  = {
    for key, value in var.secret_env_vars :
    key => value
    if !contains(keys(var.env_vars), key)
  }
}

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

      dynamic "vpc_access" {
        for_each = var.vpc_connector == "" ? [] : [1]

        content {
          connector = var.vpc_connector
          egress    = var.vpc_egress
        }
      }

      dynamic "env" {
        for_each = local.safe_env_vars

        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = local.safe_secret_env_vars
        iterator = secret_env

        content {
          name = secret_env.key

          value_source {
            secret_key_ref {
              secret  = secret_env.value
              version = "latest"
            }
          }
        }
      }
    }
  }

  ingress = var.ingress
}
