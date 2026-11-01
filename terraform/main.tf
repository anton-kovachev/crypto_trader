data "aws_caller_identity" "current" {}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_subnet" "default" {
  for_each = toset(data.aws_subnets.default.ids)
  id       = each.value
}

data "aws_internet_gateway" "default" {
  filter {
    name   = "attachment.vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

locals {
  name_prefix        = var.project_name
  default_subnet_ids = sort(data.aws_subnets.default.ids)
  lambda_subnet_ids  = [for subnet in aws_subnet.lambda_private : subnet.id]

  web_adapter_layer_arn = "arn:aws:lambda:${var.aws_region}:753240598075:layer:LambdaAdapterLayerX86:${var.lambda_web_adapter_layer_version}"

  common_tags = {
    Project = var.project_name
  }
}
