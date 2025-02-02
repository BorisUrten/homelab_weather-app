#!/bin/bash

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable is not set!"
    echo "Please create a GitHub personal access token and export it as GITHUB_TOKEN"
    exit 1
fi

# Install Flux CLI if not already installed
if ! command -v flux &> /dev/null; then
    curl -s https://fluxcd.io/install.sh | sudo bash
fi

# Bootstrap Flux
flux bootstrap github \
    --owner=$GITHUB_USER \
    --repository=weather-monitoring-system \
    --branch=main \
    --path=./gitops/clusters/my-cluster \
    --personal

# Wait for Flux to be ready
until kubectl -n flux-system get deploy/source-controller &> /dev/null; do
    echo "Waiting for Flux to be ready..."
    sleep 5
done

echo "Flux setup completed!"