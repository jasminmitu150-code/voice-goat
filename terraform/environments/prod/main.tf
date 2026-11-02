# VoiceGoat Production Environment
# Full configuration with VPN access

terraform {
  required_version = ">= 1.6.0"
  
  # Remote state for production
  backend "s3" {
    bucket         = "voicegoat-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "voicegoat-terraform-locks"
  }
}

module "voicegoat" {
  source = "../../"
  
  aws_region  = "us-east-1"
  environment = "prod"
  
  vpc_cidr   = "10.0.0.0/16"
  enable_vpn = true  # Enable VPN for secure access
  
  # Production-sized instances
  ecs_task_cpu    = 512
  ecs_task_memory = 1024
  
  opensearch_instance_type = "t3.medium.search"
  opensearch_volume_size   = 20
}

output "vpn_endpoint" {
  value = module.voicegoat.vpn_endpoint
}

output "alb_dns" {
  value = module.voicegoat.ecs_cluster_name
}
