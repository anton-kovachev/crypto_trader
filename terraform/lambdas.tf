resource "aws_cloudwatch_log_group" "backend" {
  name              = "/aws/lambda/${var.project_name}-backend"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "ui" {
  name              = "/aws/lambda/${var.project_name}-ui"
  retention_in_days = 30
}

resource "aws_lambda_function" "backend" {
  function_name = "${var.project_name}-backend"
  description   = "Processes reporter and trading_floor SQS workflows."
  role          = aws_iam_role.backend.arn
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  architectures = ["x86_64"]

  s3_bucket        = aws_s3_bucket.lambda_packages.id
  s3_key           = aws_s3_object.backend_package.key
  source_code_hash = filebase64sha256("${path.module}/../dist/backend.zip")

  timeout                        = 900
  memory_size                    = 4096
  reserved_concurrent_executions = 1

  ephemeral_storage {
    size = 2048
  }

  vpc_config {
    subnet_ids         = local.lambda_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ACCOUNT_DB_S3_BUCKET     = aws_s3_bucket.account_database.id
      ACCOUNT_DB_S3_KEY        = var.account_db_s3_key
      BACKEND_SECRETS_ARN      = var.backend_secrets_arn
      QDRANT_URL               = var.qdrant_url
      REDIS_MODE               = "elasticache"
      ELASTICACHE_HOST         = aws_elasticache_replication_group.redis.primary_endpoint_address
      ELASTICACHE_PORT         = tostring(var.redis_port)
      ELASTICACHE_USERNAME     = aws_elasticache_user.backend.user_name
      ELASTICACHE_RESOURCE_ID  = aws_elasticache_replication_group.redis.replication_group_id
      ELASTICACHE_CLUSTER_MODE = "false"
      UV_EXECUTABLE            = "/var/task/bin/uv"
      MODEL_NAME               = var.model_name
      OPENROUTER_BASE_URL      = var.openrouter_base_url
      CHAIN_ID                 = tostring(var.chain_id)
      CHAIN_NAME               = var.chain_name
      USD_TOKEN_SYMBOL         = var.usd_token_symbol
      USD_TOKEN_ADDRESS        = var.usd_token_address
      INITIAL_USDC_AMOUNT      = tostring(var.initial_usdc_amount)
      USER_ADDRESS             = var.user_address
      UNISWAP_ROUTER_ADDRESS   = var.uniswap_router_address
      TRADER_NAME              = var.trader_name
      RESEARCHER_NAME          = var.researcher_name
      REPORTER_NAME            = var.reporter_name
      PUSHOVER_API_URL         = "https://api.pushover.net/1/messages.json"
    }
  }

  depends_on = [
    aws_iam_role_policy.backend_access,
    aws_iam_role_policy_attachment.backend_logs,
    aws_iam_role_policy_attachment.backend_vpc,
    aws_s3_object.backend_package,
    aws_cloudwatch_log_group.backend,
  ]

  tags = merge(local.common_tags, { Component = "backend" })
}

resource "aws_lambda_function" "ui" {
  function_name = "${var.project_name}-ui"
  description   = "Public Gradio dashboard backed by Redis reporter data."
  role          = aws_iam_role.ui.arn
  runtime       = "python3.12"
  handler       = "run.sh"
  architectures = ["x86_64"]
  layers        = [local.web_adapter_layer_arn]

  s3_bucket        = aws_s3_bucket.lambda_packages.id
  s3_key           = aws_s3_object.ui_package.key
  source_code_hash = filebase64sha256("${path.module}/../dist/ui.zip")

  timeout     = 900
  memory_size = 2048

  ephemeral_storage {
    size = 1024
  }

  vpc_config {
    subnet_ids         = local.lambda_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      AWS_LAMBDA_EXEC_WRAPPER    = "/opt/bootstrap"
      AWS_LWA_INVOKE_MODE        = "response_stream"
      PORT                       = "8080"
      REDIS_MODE                 = "elasticache"
      ELASTICACHE_HOST           = aws_elasticache_replication_group.redis.primary_endpoint_address
      ELASTICACHE_PORT           = tostring(var.redis_port)
      ELASTICACHE_USERNAME       = aws_elasticache_user.ui.user_name
      ELASTICACHE_RESOURCE_ID    = aws_elasticache_replication_group.redis.replication_group_id
      ELASTICACHE_CLUSTER_MODE   = "false"
      UI_REFRESH_EVERY_N_SECONDS = tostring(var.ui_refresh_every_n_seconds)
      MODEL_NAME                 = var.model_name
    }
  }

  depends_on = [
    aws_iam_role_policy.ui_access,
    aws_iam_role_policy_attachment.ui_logs,
    aws_iam_role_policy_attachment.ui_vpc,
    aws_s3_object.ui_package,
    aws_cloudwatch_log_group.ui,
  ]

  tags = merge(local.common_tags, { Component = "ui" })
}

resource "aws_lambda_function_url" "ui" {
  function_name      = aws_lambda_function.ui.function_name
  authorization_type = "NONE"
  invoke_mode        = "RESPONSE_STREAM"
}

resource "aws_lambda_permission" "ui_function_url" {
  statement_id           = "AllowPublicFunctionUrl"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.ui.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "ui_function_url_invoke" {
  statement_id             = "AllowPublicFunctionUrlInvoke"
  action                   = "lambda:InvokeFunction"
  function_name            = aws_lambda_function.ui.function_name
  principal                = "*"
  invoked_via_function_url = true
}
