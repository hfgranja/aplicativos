output "ack_cluster_id" {
  value = alicloud_cs_managed_kubernetes.ack.id
}

output "acr_registry" {
  value = "registry.${var.region}.aliyuncs.com/ait"
}

output "tablestore_endpoint" {
  value = "https://${alicloud_ots_instance.ots.name}.${var.region}.ots.aliyuncs.com"
}

output "oss_assets_bucket" {
  value = alicloud_oss_bucket.assets.bucket
}
