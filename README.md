## Project Structure

The project is organized as follows:
- `app/`: Contains the Python weather monitoring application
- `gitops/`: Contains Kubernetes manifests and Flux configuration
- `k3s/`: Contains k3s setup scripts
- `scripts/`: Contains utility scripts for setup and maintenance


weather-monitoring-system/
│
├── .github/                          # GitHub Actions workflows
│   └── workflows/
│       └── docker-build.yaml         # Workflow to build and push Docker image
│
├── app/                              # Python application code
│   ├── __init__.py
│   ├── weather_app.py                # Main application file
│   ├── requirements.txt              # Python dependencies
│   └── Dockerfile                    # Dockerfile for the weather app
│
├── gitops/                           # GitOps repository structure
│   ├── clusters/
│   │   └── my-cluster/              # Your cluster configuration
│   │       ├── flux-system/         # Flux bootstrap manifests
│   │       └── weather-app/         # Application manifests
│   │           ├── namespace.yaml    # Namespace definition
│   │           ├── secrets.yaml      # Encrypted secrets
│   │           ├── configmap.yaml    # ConfigMaps
│   │           ├── postgres.yaml     # PostgreSQL StatefulSet and Service
│   │           └── deployment.yaml   # Weather app deployment
│   │
│   └── base/                        # Base Kustomize configurations
│       └── weather-app/
│           ├── kustomization.yaml
│           └── templates/            # Common templates
│           
├── k3s/                             # k3s setup scripts
│   ├── install.sh                   # k3s installation script
│   └── config/                      # k3s configuration files
│
├── scripts/                         # Utility scripts
│   ├── setup-flux.sh               # Script to setup Flux
│   └── generate-secrets.sh         # Script to generate sealed secrets
│
├── .gitignore                      # Git ignore file
├── README.md                       # Project documentation
└── .env.example                    # Example environment variables


# Weather Monitoring System

A Kubernetes-based weather monitoring system that collects and stores local weather data using GitOps practices.

## Prerequisites

- VS Code
- Docker Desktop
- kubectl
- k3s
- Flux CLI
- Git



## Setup Instructions

1. Install k3s:
```bash
./k3s/install.sh
```

2. Setup Flux:
```bash
./scripts/setup-flux.sh
```

3. Create required secrets:
```bash
./scripts/generate-secrets.sh
```

4. Build and push the Docker image:
```bash
cd app
docker build -t your-username/weather-app:latest .
docker push your-username/weather-app:latest
```

## Development

1. Create a `.env` file based on `.env.example`
2. Install Python dependencies:
```bash
pip install -r app/requirements.txt
```

3. Run the application locally:
```bash
python app/weather_app.py
```

## Monitoring

Check application status:
```bash
kubectl get pods -n weather-app
kubectl logs -f deployment/weather-app -n weather-app
```

Check database:
```bash
kubectl exec -it statefulset/postgres -n weather-app -- psql -U postgres -d weather_db -c "SELECT * FROM weather_data;"
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request


# Make scripts executable:
chmod +x k3s/install.sh
chmod +x scripts/setup-flux.sh
chmod +x scripts/generate-secrets.sh
