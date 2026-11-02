# VoiceGoat Terraform Outputs

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = module.ecs.cluster_arn
}

output "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = module.opensearch.endpoint
}

output "opensearch_dashboard_endpoint" {
  description = "OpenSearch Dashboard endpoint"
  value       = module.opensearch.dashboard_endpoint
}

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group name"
  value       = module.monitoring.log_group_name
}

output "vpn_endpoint" {
  description = "VPN Client endpoint (if enabled)"
  value       = module.vpc.vpn_endpoint
}
