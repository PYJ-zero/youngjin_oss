#!/bin/bash

helm upgrade --install loki grafana/loki-stack
helm upgrade --install loki --namespace=loki-stack grafana/loki-stack

helm upgrade --install loki grafana/loki-stack -n loki-stack \
    --set fluent-bit.enabled=true \
    -f loki-stack_values.yaml

