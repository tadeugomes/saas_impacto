output "instance_connection_name" {
  value = google_sql_database_instance.this.connection_name
}

output "instance_name" {
  value = google_sql_database_instance.this.name
}

output "private_ip_addresses" {
  value = [
    for item in google_sql_database_instance.this.ip_address : item.ip_address
    if item.type == "PRIVATE"
  ]
}

output "private_ip_address" {
  value = try(
    one([
      for item in google_sql_database_instance.this.ip_address : item.ip_address
      if item.type == "PRIVATE"
    ]),
    null
  )
}
