#!/bin/bash

# Authenticate to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 970268366635.dkr.ecr.ap-south-1.amazonaws.com

# Execute the original command (Watchtower in this case)
exec "$@"
