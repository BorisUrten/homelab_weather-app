#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    exit 1
fi

# Source the .env file
source .env

# Generate base64 encoded secrets
WEATHER_API_KEY_BASE64=$(echo -n "$WEATHER_API_KEY" | base64)
POSTGRES_USER_BASE64=$(echo -n "$DB_USER" | base64)
POSTGRES_PASSWORD_BASE64=$(echo -n "$DB_PASSWORD" | base64)

# Create the secrets directory if it doesn't exist
mkdir -p gitops/clusters/my-cluster/weather-app

# Create secrets.yaml with the encoded values
cat > gitops/clusters/my-cluster/weather-app/secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: weather-api-secret
  namespace: weather-app
type: Opaque
data:
  api-key: $WEATHER_API_KEY_BASE64
---
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: weather-app
type: Opaque
data:
  username: $POSTGRES_USER_BASE64
  password: $POSTGRES_PASSWORD_BASE64
EOF

echo "Secrets generated successfully in gitops/clusters/my-cluster/weather-app/secrets.yaml!"