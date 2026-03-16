module "cell" {
  source = "../../modules/cell-azure"

  location            = "eastus"
  cell_id             = "azure-eastus"
  environment         = "production"
  resource_group_name = "rg-ait-azure-eastus"
  aks_node_count      = 3
  aks_node_vm_size    = "Standard_D2_v3"
  cosmos_db_name      = "ait-db"
}

terraform {
  backend "azurerm" {
    resource_group_name  = "rg-ait-tfstate"
    storage_account_name = "aitterraformstate"
    container_name       = "tfstate"
    key                  = "cells/azure-eastus/terraform.tfstate"
  }
}
