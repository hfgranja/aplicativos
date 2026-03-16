terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

locals {
  tags = {
    project     = "ai-code-tester"
    cell        = var.cell_id
    environment = var.environment
  }
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.tags
}

# ── AKS Cluster ───────────────────────────────────────────────────────────────
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "ait-${var.cell_id}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "ait-${var.cell_id}"

  default_node_pool {
    name       = "general"
    node_count = var.aks_node_count
    vm_size    = var.aks_node_vm_size
  }

  identity {
    type = "SystemAssigned"
  }

  ingress_application_gateway {
    gateway_name = "ait-${var.cell_id}-agw"
    subnet_cidr  = "10.225.0.0/16"
  }

  tags = local.tags
}

# ── Azure Container Registry ──────────────────────────────────────────────────
resource "azurerm_container_registry" "acr" {
  name                = "ait${replace(var.cell_id, "-", "")}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Standard"
  admin_enabled       = false
  tags                = local.tags
}

# Grant AKS pull access to ACR
resource "azurerm_role_assignment" "aks_acr" {
  principal_id                     = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.acr.id
  skip_service_principal_aad_check = true
}

# ── Cosmos DB ─────────────────────────────────────────────────────────────────
resource "azurerm_cosmosdb_account" "cosmos" {
  name                = "ait-${var.cell_id}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.rg.location
    failover_priority = 0
  }

  tags = local.tags
}

resource "azurerm_cosmosdb_sql_database" "db" {
  name                = var.cosmos_db_name
  resource_group_name = azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.cosmos.name
}

resource "azurerm_cosmosdb_sql_container" "analyses" {
  name                = "analyses"
  resource_group_name = azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.cosmos.name
  database_name       = azurerm_cosmosdb_sql_database.db.name
  partition_key_path  = "/_partitionKey"
}

resource "azurerm_cosmosdb_sql_container" "incidents" {
  name                = "incidents"
  resource_group_name = azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.cosmos.name
  database_name       = azurerm_cosmosdb_sql_database.db.name
  partition_key_path  = "/id"
}

# ── Azure CDN ─────────────────────────────────────────────────────────────────
resource "azurerm_storage_account" "assets" {
  name                     = "ait${replace(var.cell_id, "-", "")}sa"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = local.tags
}
