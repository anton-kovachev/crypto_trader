variable "project_name" {
  description = "Prefix used for this application's AWS resources."
  type        = string
  default     = "crypto-trader"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name)) && length(var.project_name) <= 32
    error_message = "project_name must be at most 32 characters and contain only lowercase letters, digits, and hyphens."
  }
}

variable "aws_region" {
  description = "AWS region for the application."
  type        = string
  default     = "eu-north-1"
}

variable "lambda_private_subnet_cidr" {
  description = "Unused /24 CIDR inside the default VPC; split into two /25 Lambda subnets."
  type        = string
  default     = "172.31.240.0/24"
}

variable "backend_secrets_arn" {
  description = "Secrets Manager secret ARN containing backend API and wallet credentials as a JSON object."
  type        = string
}

variable "qdrant_url" {
  description = "Network-accessible Qdrant URL used by the backend MCP server."
  type        = string
}

variable "model_name" {
  description = "OpenRouter model used by all agents."
  type        = string
  default     = "gpt-5-mini"
}

variable "openrouter_base_url" {
  description = "OpenRouter OpenAI-compatible API endpoint."
  type        = string
  default     = "https://openrouter.ai/api/v1"
}

variable "chain_id" {
  description = "EVM chain ID used by the trading tools."
  type        = number
  default     = 1
}

variable "chain_name" {
  description = "EVM chain name used by the trading tools."
  type        = string
  default     = "ethereum"
}

variable "usd_token_symbol" {
  description = "Stablecoin symbol used to initialize accounts."
  type        = string
  default     = "USDC"
}

variable "usd_token_address" {
  description = "Stablecoin contract address for the selected EVM network."
  type        = string
}

variable "initial_usdc_amount" {
  description = "Initial stablecoin balance assigned when a new account is created."
  type        = number
  default     = 1000
}

variable "user_address" {
  description = "Public EVM wallet address used by the application."
  type        = string
}

variable "uniswap_router_address" {
  description = "Uniswap router contract address for the selected network."
  type        = string
}

variable "trader_name" {
  description = "Trader account and agent name."
  type        = string
  default     = "Max Kaiser"
}

variable "researcher_name" {
  description = "Researcher agent name."
  type        = string
  default     = "Guy Researcher"
}

variable "reporter_name" {
  description = "Account name reported by the reporting workflow."
  type        = string
  default     = "Max Kaiser"
}

variable "trading_schedule_expression" {
  description = "UTC EventBridge Scheduler cron expression for trading_floor."
  type        = string
  default     = "cron(0/30 * * * ? *)"
}

variable "reporting_schedule_expression" {
  description = "UTC EventBridge Scheduler cron expression for reporter."
  type        = string
  default     = "cron(5 * * * ? *)"
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type."
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_engine_version" {
  description = "ElastiCache Redis OSS engine version; IAM authentication requires Redis 7 or newer."
  type        = string
  default     = "7.1"
}

variable "redis_port" {
  description = "ElastiCache Redis port."
  type        = number
  default     = 6379
}

variable "account_db_s3_key" {
  description = "S3 object key for the SQLite account database."
  type        = string
  default     = "accounts/accounts.db"
}

variable "ui_refresh_every_n_seconds" {
  description = "How often the Gradio UI refreshes reporter data from Redis."
  type        = number
  default     = 30
}

variable "lambda_web_adapter_layer_version" {
  description = "AWS Lambda Web Adapter layer version for x86_64."
  type        = number
  default     = 30
}
