#!/bin/bash
#!/usr/local/bin/kubectl
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create ns argocd
helm install argocd argo/argo-cd -f values.yaml --namespace argocd


