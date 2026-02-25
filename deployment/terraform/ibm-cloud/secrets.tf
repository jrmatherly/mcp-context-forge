#########################
# App secrets & config
#########################

locals {
  pg_conn    = ibm_resource_key.pg_key.connection[0]
  redis_conn = ibm_resource_key.redis_key.connection[0]
}

# JWT signing secret
resource "random_password" "jwt" {
  length  = 48
  special = false
}

# Basic auth password
resource "random_password" "basic_auth" {
  length  = 24
  special = true
}

# Database connection secret (consumed by Helm chart's external postgres config)
resource "kubernetes_secret" "mcpgw_db" {
  metadata { name = "mcpgateway-db" }
  type = "Opaque"
  data = {
    host     = local.pg_conn.postgres["hosts"][0]["hostname"]
    port     = tostring(local.pg_conn.postgres["hosts"][0]["port"])
    dbname   = local.pg_conn.postgres["database"]
    user     = local.pg_conn.postgres["authentication"]["username"]
    password = local.pg_conn.postgres["authentication"]["password"]
  }
}

# Redis connection secret
resource "kubernetes_secret" "mcpgw_redis" {
  metadata { name = "mcpgateway-redis" }
  type = "Opaque"
  data = {
    REDIS_URL = local.redis_conn.rediss["composed"][0]
  }
}
