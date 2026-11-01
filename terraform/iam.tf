resource "aws_iam_role" "backend" {
  name = "${var.project_name}-backend"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role" "ui" {
  name = "${var.project_name}-ui"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role" "scheduler" {
  name = "${var.project_name}-scheduler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "backend_logs" {
  role       = aws_iam_role.backend.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "backend_vpc" {
  role       = aws_iam_role.backend.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy_attachment" "ui_logs" {
  role       = aws_iam_role.ui.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "ui_vpc" {
  role       = aws_iam_role.ui.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "backend_access" {
  name = "${var.project_name}-backend-access"
  role = aws_iam_role.backend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.account_database.arn
      },
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject"]
        Resource = [
          "${aws_s3_bucket.account_database.arn}/${var.account_db_s3_key}"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = var.backend_secrets_arn
      },
      {
        Effect = "Allow"
        Action = [
          "elasticache:Connect"
        ]
        Resource = [
          aws_elasticache_replication_group.redis.arn,
          aws_elasticache_user.backend.arn,
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility",
        ]
        Resource = [
          aws_sqs_queue.trading.arn,
          aws_sqs_queue.reporting.arn,
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy" "ui_access" {
  name = "${var.project_name}-ui-access"
  role = aws_iam_role.ui.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["elasticache:Connect"]
      Resource = [
        aws_elasticache_replication_group.redis.arn,
        aws_elasticache_user.ui.arn,
      ]
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_send" {
  name = "${var.project_name}-scheduler-send"
  role = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["sqs:SendMessage"]
      Resource = [
        aws_sqs_queue.trading.arn,
        aws_sqs_queue.reporting.arn,
        aws_sqs_queue.scheduler_delivery_dlq.arn,
      ]
    }]
  })
}
