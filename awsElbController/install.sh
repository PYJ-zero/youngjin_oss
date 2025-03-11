#!/bin/bash
##1. Policy 및 Role 생성 제외
###

#https://docs.aws.amazon.com/ko_kr/eks/latest/userguide/lbc-helm.html

##2. Controller 설치
###
helm repo add eks https://aws.github.io/eks-charts
helm repo update eks

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=my-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
