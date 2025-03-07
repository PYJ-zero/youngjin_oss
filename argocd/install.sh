#!/bin/bash
#!/usr/local/bin/kubectl

kubectl create ns argocd
kubectl apply -f pvc-argocd.yaml
helm install argocd argo/argo-cd -f values.yaml --namespace argocd


