#!/bin/bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
kubectl create ns grafana
helm install grafana grafana/grafana --namespace grafana --set adminPassword='password' --set service.type=NodePort
