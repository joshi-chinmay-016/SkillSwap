terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.20"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required GCP APIs
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "vpcaccess.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# 2. VPC Network & Private Service Connection
resource "google_compute_network" "vpc" {
  name                    = "skillswap-vpc"
  auto_create_subnetworks = true
  depends_on              = [google_project_service.services]
}

resource "google_compute_global_address" "private_ip_alloc" {
  name          = "skillswap-private-ip-alloc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

# 3. Serverless VPC Access Connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "skillswap-vpc-conn"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.name
  min_instances = 2
  max_instances = 3
  depends_on    = [google_project_service.services]
}

# 4. Artifact Registry Docker Repository
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "skillswap-repo"
  description   = "SkillSwap Arena Docker Images"
  format        = "DOCKER"
  depends_on    = [google_project_service.services]
}

# 5. Cloud SQL PostgreSQL Instance
resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "google_sql_database_instance" "db_instance" {
  name             = "skillswap-postgres-instance"
  database_version = "POSTGRES_16"
  region           = var.region

  depends_on = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier              = var.db_tier
    availability_type = "ZONAL"

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }

    backup_configuration {
      enabled    = true
      start_time = "02:00"
    }
  }
}

resource "google_sql_database" "database" {
  name     = "skillswap_prod"
  instance = google_sql_database_instance.db_instance.name
}

resource "google_sql_user" "db_user" {
  name     = "skillswap_app"
  instance = google_sql_database_instance.db_instance.name
  password = random_password.db_password.result
}

# 6. Memorystore Redis
resource "google_redis_instance" "redis_instance" {
  name           = "skillswap-redis-cache"
  tier           = "BASIC"
  memory_size_gb = var.redis_memory_size_gb
  region         = var.region

  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version     = "REDIS_7_0"
  display_name      = "SkillSwap Redis Cluster"
  depends_on        = [google_service_networking_connection.private_vpc_connection]
}

# 7. Service Accounts
resource "google_service_account" "backend_sa" {
  account_id   = "skillswap-backend-sa"
  display_name = "SkillSwap Backend Service Account"
}

resource "google_service_account" "frontend_sa" {
  account_id   = "skillswap-frontend-sa"
  display_name = "SkillSwap Frontend Service Account"
}
