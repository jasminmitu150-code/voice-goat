# OpenSearch Module Outputs

output "endpoint" {
  description = "OpenSearch domain endpoint"
  value       = aws_opensearch_domain.main.endpoint
}

output "dashboard_endpoint" {
  description = "OpenSearch Dashboard endpoint"
  value       = aws_opensearch_domain.main.dashboard_endpoint
}

output "domain_arn" {
  description = "OpenSearch domain ARN"
  value       = aws_opensearch_domain.main.arn
}

output "domain_id" {
  description = "OpenSearch domain ID"
  value       = aws_opensearch_domain.main.domain_id
}

output "dynamodb_tables" {
  description = "DynamoDB table names"
  value = {
    flags  = aws_dynamodb_table.flags.name
    users  = aws_dynamodb_table.users.name
    scores = aws_dynamodb_table.scores.name
  }
}

output "rag_bucket_name" {
  description = "S3 bucket name for RAG documents"
  value       = aws_s3_bucket.rag_documents.bucket
}

output "rag_bucket_arn" {
  description = "S3 bucket ARN for RAG documents"
  value       = aws_s3_bucket.rag_documents.arn
}
