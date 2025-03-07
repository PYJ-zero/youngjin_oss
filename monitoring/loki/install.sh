#!/bin/bash
#

helm install --values values.yaml loki --namespace=loki grafana/loki \
--set loki.useTestSchema=true \
--set grafana.enabled=false,prometheus.enabled=false,loki.persistence.enabled=true,loki.persistence.storageClassName=gp2,loki.persistence.size=5Gi
