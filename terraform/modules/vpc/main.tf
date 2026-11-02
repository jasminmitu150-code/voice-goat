# VoiceGoat VPC Module
# Creates VPC with public/private subnets and optional VPN Gateway

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpc-${var.name_suffix}"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-igw-${var.name_suffix}"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(local.azs)
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-${local.azs[count.index]}-${var.name_suffix}"
    Type = "public"
  })
}

# Private Subnets
resource "aws_subnet" "private" {
  count = length(local.azs)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = local.azs[count.index]
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-${local.azs[count.index]}-${var.name_suffix}"
    Type = "private"
  })
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat" {
  count  = var.enable_vpn ? 1 : 0
  domain = "vpc"
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat-eip-${var.name_suffix}"
  })
  
  depends_on = [aws_internet_gateway.main]
}

# NAT Gateway
resource "aws_nat_gateway" "main" {
  count = var.enable_vpn ? 1 : 0
  
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat-${var.name_suffix}"
  })
  
  depends_on = [aws_internet_gateway.main]
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-rt-${var.name_suffix}"
  })
}

# Private Route Table
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  
  dynamic "route" {
    for_each = var.enable_vpn ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.main[0].id
    }
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-rt-${var.name_suffix}"
  })
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = length(local.azs)
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = length(local.azs)
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# VPC Endpoints for AWS Services (cost optimization)
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.${data.aws_region.current.name}.s3"
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-s3-endpoint-${var.name_suffix}"
  })
}

resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.${data.aws_region.current.name}.dynamodb"
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-dynamodb-endpoint-${var.name_suffix}"
  })
}

data "aws_region" "current" {}

# Client VPN Endpoint (optional)
resource "aws_ec2_client_vpn_endpoint" "main" {
  count = var.enable_vpn ? 1 : 0
  
  description            = "VoiceGoat VPN Endpoint"
  server_certificate_arn = var.vpn_certificate_arn
  client_cidr_block      = "10.100.0.0/16"
  
  authentication_options {
    type                       = "certificate-authentication"
    root_certificate_chain_arn = var.vpn_certificate_arn
  }
  
  connection_log_options {
    enabled = false
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpn-${var.name_suffix}"
  })
}

resource "aws_ec2_client_vpn_network_association" "main" {
  count = var.enable_vpn && var.vpn_certificate_arn != "" ? 1 : 0
  
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.main[0].id
  subnet_id              = aws_subnet.private[0].id
}
