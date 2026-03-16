variable "region" {
  description = "Alibaba Cloud region"
  type        = string
  default     = "ap-east-1"
}

variable "cell_id" {
  description = "Unique cell identifier"
  type        = string
}

variable "environment" {
  type    = string
  default = "production"
}

variable "ack_node_count" {
  type    = number
  default = 3
}

variable "ack_instance_type" {
  type    = string
  default = "ecs.c6.xlarge"
}

variable "tablestore_instance" {
  description = "Alibaba Cloud Table Store instance name"
  type        = string
}
