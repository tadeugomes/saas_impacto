terraform {
  backend "gcs" {
    bucket = "saas-impacto-tfstate"
    prefix = "terraform/state"
  }
}
