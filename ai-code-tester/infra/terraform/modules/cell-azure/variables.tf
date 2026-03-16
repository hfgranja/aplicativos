variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "cell_id" {
  description = "Unique cell identifier"
  type        = string
}

variable "resource_group_name" {
  description = "Azure resource group name"
  type        = string
}

variable "environment" {
  type    = string
  default = "production"
}

variable "aks_node_count" {
  type    = number
  default = 3
}

variable "aks_node_vm_size" {
  type    = string
  default = "Standard_D2_v3"
}

variable "cosmos_db_name" {
  type    = string
  default = "ait-db"
}
