variable "region" {
  description = "IBM Cloud region for all resources (e.g. eu-gb, us-south)"
  type        = string
}

variable "prefix" {
  description = "Name prefix for all IBM Cloud assets"
  type        = string
  default     = "mcpgw"
}

variable "k8s_workers" {
  description = "Number of worker nodes per zone"
  type        = number
  default     = 1
}

variable "postgres_version" {
  description = "PostgreSQL major version"
  type        = string
  default     = "17"
}

variable "redis_version" {
  description = "Redis major version"
  type        = string
  default     = "7"
}

variable "gateway_image_repository" {
  description = "OCI image repository for the MCP Gateway container"
  type        = string
  default     = "ghcr.io/jrmatherly/mcp-context-forge"
}

variable "gateway_image_tag" {
  description = "OCI image tag for the MCP Gateway container"
  type        = string
  default     = "latest"
}

variable "chart_version" {
  description = "Helm chart version to deploy"
  type        = string
  default     = "1.0.0-rc.1"
}

variable "gateway_replicas" {
  description = "Number of MCP Gateway pods"
  type        = number
  default     = 2
}

variable "auth_required" {
  description = "Require authentication for API access"
  type        = bool
  default     = true
}

variable "plugins_enabled" {
  description = "Enable the plugin framework (security plugins, rate limiting, etc.)"
  type        = bool
  default     = true
}
