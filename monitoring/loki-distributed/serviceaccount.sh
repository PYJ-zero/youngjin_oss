#!/bin/bash

eksctl create iamserviceaccount --name loki-s3 --namespace loki-distributed --cluster {your-cluster-name} --role-name {your-role-name} \
	--attach-policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess --approve

