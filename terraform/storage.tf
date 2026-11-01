resource "aws_s3_bucket" "account_database" {
  bucket        = "${var.project_name}-account-db-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
  tags          = merge(local.common_tags, { Data = "account-database" })
}

resource "aws_s3_bucket" "lambda_packages" {
  bucket        = "${var.project_name}-lambda-packages-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
  tags          = merge(local.common_tags, { Data = "lambda-packages" })
}

resource "aws_s3_bucket_public_access_block" "account_database" {
  bucket                  = aws_s3_bucket.account_database.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "lambda_packages" {
  bucket                  = aws_s3_bucket.lambda_packages.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "account_database" {
  bucket = aws_s3_bucket.account_database.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_packages" {
  bucket = aws_s3_bucket.lambda_packages.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "account_database" {
  bucket = aws_s3_bucket.account_database.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "account_database" {
  bucket = aws_s3_bucket.account_database.id

  rule {
    id     = "expire-old-database-versions"
    status = "Enabled"

    filter {
      prefix = ""
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_s3_bucket_policy" "account_database_tls" {
  bucket = aws_s3_bucket.account_database.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource = [
        aws_s3_bucket.account_database.arn,
        "${aws_s3_bucket.account_database.arn}/*",
      ]
      Condition = {
        Bool = {
          "aws:SecureTransport" = "false"
        }
      }
    }]
  })

  depends_on = [aws_s3_bucket_public_access_block.account_database]
}

resource "aws_s3_object" "backend_package" {
  bucket       = aws_s3_bucket.lambda_packages.id
  key          = "backend/backend.zip"
  source       = "${path.module}/../dist/backend.zip"
  source_hash  = filebase64sha256("${path.module}/../dist/backend.zip")
  content_type = "application/zip"
}

resource "aws_s3_object" "ui_package" {
  bucket       = aws_s3_bucket.lambda_packages.id
  key          = "ui/ui.zip"
  source       = "${path.module}/../dist/ui.zip"
  source_hash  = filebase64sha256("${path.module}/../dist/ui.zip")
  content_type = "application/zip"
}
