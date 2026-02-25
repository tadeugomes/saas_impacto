output "service_id" {
  description = "Resource id of the Cloud Run service."
  value       = google_cloud_run_v2_service.this.id
}

output "service_url" {
  description = "Service URL."
  value       = google_cloud_run_v2_service.this.uri
}
