variable "project_id" {
  type        = string
  description = "The Google Cloud Platform Project ID"
}

variable "region" {
  type        = string
  description = "Default GCP Region for compute and managed data services"
  default     = "us-central1"
}

variable "db_tier" {
  type        = string
  description = "Cloud SQL PostgreSQL machine tier (db-f1-micro for cost optimization / dev, db-custom-2-7680 for prod)"
  default     = "db-f1-micro"
}

variable "redis_memory_size_gb" {
  type        = number
  description = "Memorystore Redis instance size in GB"
  default     = 1
}
