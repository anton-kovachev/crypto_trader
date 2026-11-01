resource "aws_elasticache_subnet_group" "redis" {
  name        = "${var.project_name}-redis"
  description = "Default VPC subnets for the crypto-trader Redis cluster"
  subnet_ids  = local.default_subnet_ids
}

resource "aws_elasticache_user" "backend" {
  user_id       = "${var.project_name}-backend"
  user_name     = "${var.project_name}-backend"
  engine        = "redis"
  access_string = "on ~accounts +@read +@write +ping +client|setinfo"

  authentication_mode {
    type = "iam"
  }
}

resource "aws_elasticache_user" "ui" {
  user_id       = "${var.project_name}-ui"
  user_name     = "${var.project_name}-ui"
  engine        = "redis"
  access_string = "on ~accounts +@read +ping +client|setinfo"

  authentication_mode {
    type = "iam"
  }
}

resource "aws_elasticache_user" "default" {
  user_id       = "${var.project_name}-default"
  user_name     = "default"
  engine        = "redis"
  access_string = "off -@all"

  authentication_mode {
    type = "no-password-required"
  }
}

resource "aws_elasticache_user_group" "application" {
  user_group_id = "${var.project_name}-users"
  engine        = "redis"
  user_ids = [
    aws_elasticache_user.default.user_id,
    aws_elasticache_user.backend.user_id,
    aws_elasticache_user.ui.user_id,
  ]
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.project_name}-redis"
  description                = "Redis mediator for crypto-trader reporter data"
  engine                     = "redis"
  engine_version             = var.redis_engine_version
  node_type                  = var.redis_node_type
  num_cache_clusters         = 1
  port                       = var.redis_port
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.redis.id]
  user_group_ids             = [aws_elasticache_user_group.application.user_group_id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  transit_encryption_mode    = "required"
  automatic_failover_enabled = false
  multi_az_enabled           = false
  snapshot_retention_limit   = 1
  apply_immediately          = true

  tags = local.common_tags
}
