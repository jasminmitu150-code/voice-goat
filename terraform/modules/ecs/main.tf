# VoiceGoat ECS Module
# Creates ECS Fargate cluster with ALB and task definitions

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.name_prefix}-cluster-${var.name_suffix}"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cluster-${var.name_suffix}"
  })
}

# ECS Cluster Capacity Providers
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name
  
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name        = "${var.name_prefix}-alb-sg-${var.name_suffix}"
  description = "Security group for VoiceGoat ALB"
  vpc_id      = var.vpc_id
  
  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
  
  ingress {
    description = "HTTP from VPC (redirect to HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb-sg-${var.name_suffix}"
  })
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.name_prefix}-ecs-sg-${var.name_suffix}"
  description = "Security group for VoiceGoat ECS tasks"
  vpc_id      = var.vpc_id
  
  ingress {
    description     = "Traffic from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-ecs-sg-${var.name_suffix}"
  })
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.name_prefix}-alb-${var.name_suffix}"
  internal           = true  # Private VPC only
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.private_subnet_ids
  
  enable_deletion_protection = false
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb-${var.name_suffix}"
  })
}

# ALB Target Groups (one per service)
resource "aws_lb_target_group" "voicebank" {
  name        = "${var.name_prefix}-bank-tg-${var.name_suffix}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }
  
  tags = merge(var.tags, {
    Name    = "${var.name_prefix}-bank-tg-${var.name_suffix}"
    Service = "voicebank"
  })
}

resource "aws_lb_target_group" "voiceadmin" {
  name        = "${var.name_prefix}-admin-tg-${var.name_suffix}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }
  
  tags = merge(var.tags, {
    Name    = "${var.name_prefix}-admin-tg-${var.name_suffix}"
    Service = "voiceadmin"
  })
}

resource "aws_lb_target_group" "voicerag" {
  name        = "${var.name_prefix}-rag-tg-${var.name_suffix}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }
  
  tags = merge(var.tags, {
    Name    = "${var.name_prefix}-rag-tg-${var.name_suffix}"
    Service = "voicerag"
  })
}

resource "aws_lb_target_group" "dashboard" {
  name        = "${var.name_prefix}-dash-tg-${var.name_suffix}"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }
  
  tags = merge(var.tags, {
    Name    = "${var.name_prefix}-dash-tg-${var.name_suffix}"
    Service = "dashboard"
  })
}

# ALB Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.dashboard.arn
  }
}

# Path-based routing rules
resource "aws_lb_listener_rule" "voicebank" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.voicebank.arn
  }
  
  condition {
    path_pattern {
      values = ["/api/voicebank/*", "/voicebank/*"]
    }
  }
}

resource "aws_lb_listener_rule" "voiceadmin" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 101
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.voiceadmin.arn
  }
  
  condition {
    path_pattern {
      values = ["/api/voiceadmin/*", "/voiceadmin/*"]
    }
  }
}

resource "aws_lb_listener_rule" "voicerag" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 102
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.voicerag.arn
  }
  
  condition {
    path_pattern {
      values = ["/api/voicerag/*", "/voicerag/*"]
    }
  }
}

# IAM Role for ECS Tasks
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.name_prefix}-ecs-exec-${var.name_suffix}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role for ECS Tasks (runtime)
resource "aws_iam_role" "ecs_task" {
  name = "${var.name_prefix}-ecs-task-${var.name_suffix}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

# INTENTIONALLY OVERPRIVILEGED - Part of LLM06 demonstration
resource "aws_iam_role_policy" "ecs_task_bedrock" {
  name = "${var.name_prefix}-bedrock-policy"
  role = aws_iam_role.ecs_task.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Bedrock access
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      },
      {
        # Transcribe access
        Effect = "Allow"
        Action = [
          "transcribe:StartStreamTranscription",
          "transcribe:StartTranscriptionJob",
          "transcribe:GetTranscriptionJob"
        ]
        Resource = "*"
      },
      {
        # Polly access
        Effect = "Allow"
        Action = [
          "polly:SynthesizeSpeech"
        ]
        Resource = "*"
      },
      {
        # DynamoDB access - INTENTIONALLY OVERPRIVILEGED (LLM06)
        Effect = "Allow"
        Action = [
          "dynamodb:*"  # Should be GetItem, PutItem only
        ]
        Resource = "*"
      },
      {
        # S3 access
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = "*"
      },
      {
        # CloudWatch Logs
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.name_prefix}-${var.name_suffix}"
  retention_in_days = 7
  
  tags = var.tags
}
