# VoiceGoat Monitoring Module
# CloudWatch dashboards, alarms, and X-Ray configuration

# CloudWatch Log Group for application logs
resource "aws_cloudwatch_log_group" "app" {
  name              = "/voicegoat/${var.name_prefix}-${var.name_suffix}"
  retention_in_days = 7
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-logs-${var.name_suffix}"
  })
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.name_prefix}-dashboard-${var.name_suffix}"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 1
        properties = {
          markdown = "# 🐐 VoiceGoat Security Training Dashboard\n**Warning: This application is intentionally vulnerable**"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "Flags Captured"
          region = var.aws_region
          metrics = [
            ["VoiceGoat", "FlagsCaptured", "Service", "voicebank"],
            [".", ".", ".", "voiceadmin"],
            [".", ".", ".", "voicerag"]
          ]
          stat   = "Sum"
          period = 300
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "Attack Attempts"
          region = var.aws_region
          metrics = [
            ["VoiceGoat", "AttackAttempts", "Type", "prompt_injection"],
            [".", ".", ".", "excessive_agency"],
            [".", ".", ".", "rag_poisoning"]
          ]
          stat   = "Sum"
          period = 300
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 1
        width  = 8
        height = 6
        properties = {
          title  = "LLM Invocations"
          region = var.aws_region
          metrics = [
            ["AWS/Bedrock", "Invocations"]
          ]
          stat   = "Sum"
          period = 300
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 7
        width  = 24
        height = 6
        properties = {
          title  = "Recent Attack Logs"
          region = var.aws_region
          query  = "SOURCE '/voicegoat/${var.name_prefix}-${var.name_suffix}' | fields @timestamp, @message | filter @message like /FLAG|attack|injection|exploit/ | sort @timestamp desc | limit 50"
        }
      }
    ]
  })
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.name_prefix}-alerts-${var.name_suffix}"
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alerts-${var.name_suffix}"
  })
}

# CloudWatch Alarm - High Error Rate
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.name_prefix}-high-errors-${var.name_suffix}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "VoiceGoat"
  period              = 300
  statistic           = "Sum"
  threshold           = 100
  alarm_description   = "High error rate detected - possible attack in progress"
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
  
  tags = var.tags
}

# CloudWatch Alarm - Unusual LLM Usage (DoS/DoW detection)
resource "aws_cloudwatch_metric_alarm" "llm_throttling" {
  alarm_name          = "${var.name_prefix}-llm-throttle-${var.name_suffix}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "InvocationThrottles"
  namespace           = "AWS/Bedrock"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "LLM throttling detected - possible DoS attack"
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  
  tags = var.tags
}

# X-Ray Sampling Rule
resource "aws_xray_sampling_rule" "main" {
  rule_name      = "${var.name_prefix}-sampling-${var.name_suffix}"
  priority       = 1000
  version        = 1
  reservoir_size = 5
  fixed_rate     = 0.1
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"
  
  tags = var.tags
}

# Metric Filters for Attack Detection
resource "aws_cloudwatch_log_metric_filter" "prompt_injection" {
  name           = "${var.name_prefix}-prompt-injection"
  pattern        = "[timestamp, level, message = \"*prompt*injection*\" || message = \"*ignore*previous*\" || message = \"*system*prompt*\"]"
  log_group_name = aws_cloudwatch_log_group.app.name
  
  metric_transformation {
    name          = "PromptInjectionAttempts"
    namespace     = "VoiceGoat"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "flag_capture" {
  name           = "${var.name_prefix}-flag-capture"
  pattern        = "[timestamp, level, message = \"*FLAG{*\"]"
  log_group_name = aws_cloudwatch_log_group.app.name
  
  metric_transformation {
    name          = "FlagsFound"
    namespace     = "VoiceGoat"
    value         = "1"
    default_value = "0"
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}
