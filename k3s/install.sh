#!/bin/bash

# Install k3s
curl -sfL https://get.k3s.io | sh -

# Wait for k3s to be ready
until kubectl get nodes; do
    echo "Waiting for k3s to be ready..."
    sleep 5
done

# Copy kubeconfig to user's home directory
mkdir -p $HOME/.kube
sudo cp /etc/rancher/k3s/k3s.yaml $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

echo "k3s installation completed!"