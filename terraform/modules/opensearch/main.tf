# VoiceGoat OpenSearch Module
# Creates OpenSearch domain for RAG vector storage
# INTENTIONALLY MISCONFIGURED for LLM08 demonstrations

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Security Group for OpenSearch
resource "aws_security_group" "opensearch" {
  name        = "${var.name_prefix}-opensearch-sg-${var.name_suffix}"
  description = "Security group for VoiceGoat OpenSearch"
  vpc_id      = var.vpc_id
  
  # INTENTIONALLY OVERLY PERMISSIVE - LLM08 demonstration
  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # Should be more restrictive
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-opensearch-sg-${var.name_suffix}"
  })
}

# OpenSearch Domain
resource "aws_opensearch_domain" "main" {
  domain_name    = "${var.name_prefix}-${var.name_suffix}"
  engine_version = "OpenSearch_2.11"
  
  cluster_config {
    instance_type  = var.instance_type
    instance_count = 1
    
    zone_awareness_enabled = false
  }
  
  ebs_options {
    ebs_enabled = true
    volume_size = var.volume_size
    volume_type = "gp3"
  }
  
  vpc_options {
    subnet_ids         = [var.private_subnet_ids[0]]
    security_group_ids = [aws_security_group.opensearch.id]
  }
  
  # INTENTIONALLY WEAK ACCESS POLICY - LLM08 demonstration
  # In production, this should be much more restrictive
  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "*"  # VULNERABLE: Should specify specific roles
        }
        Action   = "es:*"  # VULNERABLE: Should be read-only for most users
        Resource = "arn:aws:es:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:domain/${var.name_prefix}-${var.name_suffix}/*"
      }
    ]
  })
  
  encrypt_at_rest {
    enabled = true
  }
  
  node_to_node_encryption {
    enabled = true
  }
  
  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }
  
  # INTENTIONALLY DISABLED - LLM08 demonstration
  # Fine-grained access control would prevent cross-tenant access
  advanced_security_options {
    enabled                        = false  # VULNERABLE: Should be true
    internal_user_database_enabled = false
  }
  
  tags = merge(var.tags, {
    Name     = "${var.name_prefix}-opensearch-${var.name_suffix}"
    Warning  = "INTENTIONALLY MISCONFIGURED"
    Vuln     = "LLM08"
  })
}

# DynamoDB Tables for Flags and Users
resource "aws_dynamodb_table" "flags" {
  name           = "${var.name_prefix}-flags-${var.name_suffix}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "flag_id"
  
  attribute {
    name = "flag_id"
    type = "S"
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-flags-${var.name_suffix}"
  })
}

resource "aws_dynamodb_table" "users" {
  name           = "${var.name_prefix}-users-${var.name_suffix}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  
  attribute {
    name = "user_id"
    type = "S"
  }
  
  # INTENTIONALLY NO ENCRYPTION - Security training demonstration
  # server_side_encryption {
  #   enabled = true
  # }
  
  tags = merge(var.tags, {
    Name    = "${var.name_prefix}-users-${var.name_suffix}"
    Warning = "INTENTIONALLY INSECURE"
  })
}

resource "aws_dynamodb_table" "scores" {
  name           = "${var.name_prefix}-scores-${var.name_suffix}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "flag_id"
  
  attribute {
    name = "user_id"
    type = "S"
  }
  
  attribute {
    name = "flag_id"
    type = "S"
  }
  
  global_secondary_index {
    name            = "flag-index"
    hash_key        = "flag_id"
    projection_type = "ALL"
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-scores-${var.name_suffix}"
  })
}

# S3 Bucket for RAG documents - INTENTIONALLY MISCONFIGURED
resource "aws_s3_bucket" "rag_documents" {
  bucket = "${var.name_prefix}-rag-docs-${var.name_suffix}"
  
  tags = merge(var.tags, {
    Name    = "${var.name_prefix}-rag-docs-${var.name_suffix}"
    Warning = "INTENTIONALLY MISCONFIGURED"
    Vuln    = "LLM08"
  })
}

# INTENTIONALLY NO BUCKET POLICY - allows overly broad access
# In production, this should have a restrictive bucket policy

resource "aws_s3_bucket_versioning" "rag_documents" {
  bucket = aws_s3_bucket.rag_documents.id
  versioning_configuration {
    status = "Disabled"  # VULNERABLE: Should be enabled
  }
}

# INTENTIONALLY PUBLIC READ - for RAG poisoning demonstration
resource "aws_s3_bucket_public_access_block" "rag_documents" {
  bucket = aws_s3_bucket.rag_documents.id
  
  block_public_acls       = false  # VULNERABLE
  block_public_policy     = false  # VULNERABLE
  ignore_public_acls      = false  # VULNERABLE
  restrict_public_buckets = false  # VULNERABLE
}
