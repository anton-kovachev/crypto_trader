resource "aws_sqs_queue" "trading_dlq" {
  name                      = "${var.project_name}-trading-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue" "reporting_dlq" {
  name                      = "${var.project_name}-reporting-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue" "scheduler_delivery_dlq" {
  name                      = "${var.project_name}-scheduler-delivery-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue" "trading" {
  name                       = "${var.project_name}-trading"
  message_retention_seconds  = 1209600
  receive_wait_time_seconds  = 10
  visibility_timeout_seconds = 5400
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.trading_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "reporting" {
  name                       = "${var.project_name}-reporting"
  message_retention_seconds  = 1209600
  receive_wait_time_seconds  = 10
  visibility_timeout_seconds = 5400
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.reporting_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_scheduler_schedule_group" "application" {
  name = var.project_name
}

resource "aws_scheduler_schedule" "trading" {
  name                         = "${var.project_name}-trading"
  group_name                   = aws_scheduler_schedule_group.application.name
  schedule_expression          = var.trading_schedule_expression
  schedule_expression_timezone = "UTC"
  state                        = "ENABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_sqs_queue.trading.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({ workflow = "trading_floor" })

    dead_letter_config {
      arn = aws_sqs_queue.scheduler_delivery_dlq.arn
    }

    retry_policy {
      maximum_event_age_in_seconds = 3600
      maximum_retry_attempts       = 3
    }
  }

  depends_on = [aws_iam_role_policy.scheduler_send]
}

resource "aws_scheduler_schedule" "reporting" {
  name                         = "${var.project_name}-reporting"
  group_name                   = aws_scheduler_schedule_group.application.name
  schedule_expression          = var.reporting_schedule_expression
  schedule_expression_timezone = "UTC"
  state                        = "ENABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_sqs_queue.reporting.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({ workflow = "reporter" })

    dead_letter_config {
      arn = aws_sqs_queue.scheduler_delivery_dlq.arn
    }

    retry_policy {
      maximum_event_age_in_seconds = 3600
      maximum_retry_attempts       = 3
    }
  }

  depends_on = [aws_iam_role_policy.scheduler_send]
}

resource "aws_lambda_event_source_mapping" "trading" {
  event_source_arn        = aws_sqs_queue.trading.arn
  function_name           = aws_lambda_function.backend.arn
  batch_size              = 1
  function_response_types = ["ReportBatchItemFailures"]
  enabled                 = true
}

resource "aws_lambda_event_source_mapping" "reporting" {
  event_source_arn        = aws_sqs_queue.reporting.arn
  function_name           = aws_lambda_function.backend.arn
  batch_size              = 1
  function_response_types = ["ReportBatchItemFailures"]
  enabled                 = true
}
