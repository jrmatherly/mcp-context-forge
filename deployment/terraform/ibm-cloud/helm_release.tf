##################################
# Deploy the application via Helm
##################################
resource "helm_release" "mcpgw" {
  name       = "mcpgateway"
  repository = "oci://ghcr.io/jrmatherly/mcp-context-forge"
  chart      = "mcp-stack"
  version    = var.chart_version

  values = [
    yamlencode({
      mcpContextForge = {
        image = {
          repository = var.gateway_image_repository
          tag        = var.gateway_image_tag
          pullPolicy = "IfNotPresent"
        }
        replicaCount = var.gateway_replicas

        pluginConfig = {
          enabled = var.plugins_enabled
        }

        ingress = {
          enabled   = true
          className = "public-iks-k8s-nginx"
          host      = "gateway.${var.prefix}.apps.${var.region}.containers.appdomain.cloud"
          path      = "/"
          tls = {
            enabled = true
          }
        }

        secret = {
          JWT_SECRET_KEY      = random_password.jwt.result
          BASIC_AUTH_USER     = "admin"
          BASIC_AUTH_PASSWORD = random_password.basic_auth.result
        }

        config = {
          AUTH_REQUIRED   = tostring(var.auth_required)
          PLUGINS_ENABLED = tostring(var.plugins_enabled)
          LOG_LEVEL       = "INFO"
        }
      }

      postgres = {
        external = {
          enabled        = true
          existingSecret = kubernetes_secret.mcpgw_db.metadata[0].name
        }
      }

      redis = {
        external = {
          enabled        = true
          existingSecret = kubernetes_secret.mcpgw_redis.metadata[0].name
        }
      }
    })
  ]
}
