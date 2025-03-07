#!/bin/bash
#
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm -n mimir-test install mimir grafana/mimir-distributed
