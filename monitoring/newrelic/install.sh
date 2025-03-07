#!/bin/bash
#

KSM_IMAGE_VERSION="v2.10.0" && \
helm repo add newrelic https://helm-charts.newrelic.com && helm repo update && \
kubectl create namespace newrelic ; helm upgrade --install newrelic-bundle newrelic/nri-bundle \
 --set global.licenseKey={your-license-key} \
 --set global.cluster={your-cluster-name} \
 --namespace=newrelic \
 --set newrelic-infrastructure.privileged=true \
 --set global.lowDataMode=true \
 --set kube-state-metrics.image.tag=${KSM_IMAGE_VERSION} \
 --set kube-state-metrics.enabled=true \
 --set kubeEvents.enabled=true \
 --set logging.enabled=true \
 --set newrelic-logging.lowDataMode=true 
