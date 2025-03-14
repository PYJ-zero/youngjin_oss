#!/bin/bash
##1. Policy 및 Role 생성 제외
###

#https://docs.aws.amazon.com/ko_kr/eks/latest/userguide/lbc-helm.html
# terraform으로 미리 생성해 두었음

##2. SA 생성
kubectl apply -f 0_sa.yaml

##3. Controller 설치
###
helm repo add eks https://aws.github.io/eks-charts
helm repo update eks

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName={your-cluster-name} \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
