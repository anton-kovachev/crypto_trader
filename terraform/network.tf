resource "aws_subnet" "lambda_private" {
  count                   = 2
  vpc_id                  = data.aws_vpc.default.id
  cidr_block              = cidrsubnet(var.lambda_private_subnet_cidr, 1, count.index)
  availability_zone       = data.aws_subnet.default[local.default_subnet_ids[count.index]].availability_zone
  map_public_ip_on_launch = false

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-lambda-private-${count.index + 1}"
  })
}

resource "aws_eip" "lambda_nat" {
  domain = "vpc"
  tags   = merge(local.common_tags, { Name = "${local.name_prefix}-nat-eip" })
}

resource "aws_nat_gateway" "lambda" {
  allocation_id = aws_eip.lambda_nat.id
  subnet_id     = local.default_subnet_ids[0]

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-nat" })

  depends_on = [data.aws_internet_gateway.default]
}

resource "aws_route_table" "lambda_private" {
  vpc_id = data.aws_vpc.default.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.lambda.id
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-lambda-private" })
}

resource "aws_route_table_association" "lambda_private" {
  count          = 2
  subnet_id      = aws_subnet.lambda_private[count.index].id
  route_table_id = aws_route_table.lambda_private.id
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = data.aws_vpc.default.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.lambda_private.id]

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-s3-endpoint" })
}

resource "aws_security_group" "lambda" {
  name        = "${local.name_prefix}-lambda"
  description = "Lambda egress for Redis and external APIs"
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_security_group" "redis" {
  name        = "${local.name_prefix}-redis"
  description = "Redis accepts connections only from this application's Lambdas"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port       = var.redis_port
    to_port         = var.redis_port
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}
