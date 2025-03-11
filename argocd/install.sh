#!/bin/bash
#!/usr/local/bin/kubectl

kubectl create ns argocd
helm install argocd argo/argo-cd -f values.yaml --namespace argocd


