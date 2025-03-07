#!/bin/bash

helm install grafana grafana/grafana --namespace grafana --set adminPassword='password' --set service.type=NodePort
