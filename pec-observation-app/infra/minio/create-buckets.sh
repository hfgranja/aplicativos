#!/bin/sh
set -e

MC=/usr/bin/mc
MINIO_ALIAS=local
MINIO_URL=${MINIO_ENDPOINT:-http://minio:9000}
MINIO_ACCESS=${MINIO_ROOT_USER:-minioadmin}
MINIO_SECRET=${MINIO_ROOT_PASSWORD:-minioadmin}

until $MC alias set $MINIO_ALIAS $MINIO_URL $MINIO_ACCESS $MINIO_SECRET; do
  echo "Waiting for MinIO..."
  sleep 2
done

$MC mb --ignore-existing $MINIO_ALIAS/audio-uploads
$MC mb --ignore-existing $MINIO_ALIAS/pdf-exports

$MC anonymous set download $MINIO_ALIAS/pdf-exports

echo "MinIO buckets ready."
