# VoiceGoat Development Environment
# Minimal configuration for development and testing

terraform {
  required_version = ">= 1.6.0"
}

module "voicegoat" {
  source = "../../"
  
  aws_region  = "us-east-1"
  environment = "dev"
  
  vpc_cidr   = "10.0.0.0/16"
  enable_vpn = false  # Disable VPN for dev environment
  
  # Smaller instances for cost savings
  ecs_task_cpu    = 256
  ecs_task_memory = 512
  
  opensearch_instance_type = "t3.small.search"
  opensearch_volume_size   = 10
}

output "alb_endpoint" {
  value = module.voicegoat.ecs_cluster_name
}
