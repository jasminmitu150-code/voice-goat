# VPC Module Outputs

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "internet_gateway_id" {
  description = "Internet Gateway ID"
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_id" {
  description = "NAT Gateway ID"
  value       = var.enable_vpn ? aws_nat_gateway.main[0].id : null
}

output "vpn_endpoint" {
  description = "VPN Client Endpoint ID"
  value       = var.enable_vpn && length(aws_ec2_client_vpn_endpoint.main) > 0 ? aws_ec2_client_vpn_endpoint.main[0].id : null
}
