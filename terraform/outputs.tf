output "ui_url" {
  description = "Public Gradio UI Function URL. Anyone with this URL can access reporter data."
  value       = aws_lambda_function_url.ui.function_url
}

output "backend_lambda_name" {
  description = "Name of the shared backend Lambda."
  value       = aws_lambda_function.backend.function_name
}

output "account_database_bucket" {
  description = "S3 bucket storing the SQLite account database."
  value       = aws_s3_bucket.account_database.id
}

output "account_database_key" {
  description = "S3 object key storing the SQLite account database."
  value       = var.account_db_s3_key
}

output "redis_primary_endpoint" {
  description = "Private ElastiCache Redis endpoint."
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "trading_queue_url" {
  description = "SQS queue receiving trading_floor schedule messages."
  value       = aws_sqs_queue.trading.url
}

output "reporting_queue_url" {
  description = "SQS queue receiving reporter schedule messages."
  value       = aws_sqs_queue.reporting.url
}

output "trading_schedule_expression" {
  description = "Cron expression used by the trading_floor schedule."
  value       = var.trading_schedule_expression
}

output "reporting_schedule_expression" {
  description = "Cron expression used by the reporter schedule."
  value       = var.reporting_schedule_expression
}
