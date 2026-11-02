# VoiceGoat Terraform Root Module
# This file orchestrates all infrastructure modules

terraform {
  required_version = ">= 1.6.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
  
  # Backend configuration - uncomment for remote state
  # backend "s3" {
  #   bucket         = "voicegoat-terraform-state"
  #   key            = "terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "voicegoat-terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "VoiceGoat"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Purpose     = "Security Training"
      Warning     = "INTENTIONALLY VULNERABLE"
    }
  }
}

# Random suffix for unique resource names
resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  name_prefix = "voicegoat-${var.environment}"
  name_suffix = random_id.suffix.hex
  
  common_tags = {
    Project     = "VoiceGoat"
    Environment = var.environment
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  name_prefix    = local.name_prefix
  name_suffix    = local.name_suffix
  environment    = var.environment
  vpc_cidr       = var.vpc_cidr
  enable_vpn     = var.enable_vpn
  
  tags = local.common_tags
}

# ECS Cluster Module
module "ecs" {
  source = "./modules/ecs"
  
  name_prefix         = local.name_prefix
  name_suffix         = local.name_suffix
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  
  tags = local.common_tags
}

# OpenSearch Module (for RAG)
module "opensearch" {
  source = "./modules/opensearch"
  
  name_prefix        = local.name_prefix
  name_suffix        = local.name_suffix
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  
  tags = local.common_tags
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"
  
  name_prefix = local.name_prefix
  name_suffix = local.name_suffix
  environment = var.environment
  
  tags = local.common_tags
}
