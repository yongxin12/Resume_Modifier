#!/bin/bash

OCI_REGION_KEY="yyz"
OCI_TENANCY_NAMESPACE="yztdqx0npeqw"
OCI_REPO_NAME="editor-backend"
TAG="latest"
OCIR_URL="${OCI_REGION_KEY}.ocir.io/${OCI_TENANCY_NAMESPACE}"

docker login ${OCI_REGION_KEY}.ocir.io

docker buildx create --use

docker buildx build --platform linux/arm64,linux/amd64 -f Dockerfile.prod -t ${OCIR_URL}/${OCI_REPO_NAME}:${TAG} --push .


