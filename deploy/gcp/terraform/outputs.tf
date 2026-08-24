output "artifact_registry_repo" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.name}"
  description = "Artifact Registry image path"
}

output "cloud_sql_private_ip" {
  value       = google_sql_database_instance.db_instance.private_ip_address
  description = "Private IP address of Cloud SQL instance"
}

output "redis_host" {
  value       = google_redis_instance.redis_instance.host
  description = "Private IP host of Memorystore Redis"
}

output "vpc_connector_name" {
  value       = google_vpc_access_connector.connector.name
  description = "Serverless VPC Connector name"
}
