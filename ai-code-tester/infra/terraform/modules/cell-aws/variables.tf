variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cell_id" {
  description = "Unique cell identifier"
  type        = string
}

variable "environment" {
  description = "Environment name (production, staging)"
  type        = string
  default     = "production"
}

variable "eks_node_instance_type" {
  description = "EC2 instance type for EKS nodes"
  type        = string
  default     = "m5.large"
}

variable "eks_node_count" {
  description = "Number of EKS worker nodes"
  type        = number
  default     = 3
}

variable "dynamodb_table_analyses" {
  description = "DynamoDB table name for analyses"
  type        = string
  default     = "ait-analyses"
}

variable "dynamodb_table_incidents" {
  description = "DynamoDB table name for incidents"
  type        = string
  default     = "ait-incidents"
}
