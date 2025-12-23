# Architecture Documentation

## Overview

The Weather Monitoring System is a cloud-native application designed to demonstrate production-grade Kubernetes deployment patterns, GitOps workflows, and modern observability practices.

## Design Principles

### 1. Cloud-Native First
- **Containerized**: All components run in containers
- **Kubernetes-Native**: Leverages native K8s resources (Deployments, StatefulSets, Services)
- **12-Factor App**: Follows twelve-factor app methodology
- **Stateless Application**: Weather app is stateless, enabling horizontal scaling

### 2. GitOps Philosophy
- **Declarative Infrastructure**: All infrastructure defined as code
- **Git as Source of Truth**: Repository is the single source of truth
- **Automated Synchronization**: Flux CD keeps cluster in sync with Git
- **Separation of Concerns**: Application code and infrastructure separated

### 3. Observability
- **Metrics**: Prometheus metrics for monitoring
- **Logging**: Structured logging for troubleshooting
- **Health Checks**: Liveness and readiness probes
- **Tracing**: Ready for distributed tracing integration

---

## Component Architecture

### Weather Application

**Language**: Python 3.9  
**Framework**: Native Python with minimal dependencies  
**Deployment**: Kubernetes Deployment (stateless)

#### Key Features:
- Polls WeatherAPI.com at configurable intervals
- Stores data in PostgreSQL
- Exposes Prometheus metrics
- Implements health check endpoints
- Graceful shutdown handling

#### Endpoints:
- `/health` - Liveness probe (port 8080)
- `/ready` - Readiness probe (port 8080)
- `/metrics` - Prometheus metrics (port 8080)

#### Environment Variables:
- `WEATHER_API_KEY` - API key for WeatherAPI.com (from Secret)
- `DB_HOST` - PostgreSQL host
- `DB_NAME` - Database name
- `DB_USER` - Database username (from Secret)
- `DB_PASSWORD` - Database password (from Secret)
- `CITY` - City to monitor (from ConfigMap)
- `COUNTRY` - Country (from ConfigMap)
- `UPDATE_INTERVAL` - Polling interval in seconds (default: 300)
- `HEALTH_PORT` - Health check server port (default: 8080)

### PostgreSQL Database

**Version**: PostgreSQL 14 Alpine  
**Deployment**: StatefulSet with persistent volume  
**Storage**: 1Gi PersistentVolumeClaim

#### Schema:
```sql
CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    temperature FLOAT NOT NULL,
    humidity FLOAT,
    pressure FLOAT,
    timestamp TIMESTAMP NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL
);
```

#### Design Decisions:
- **StatefulSet** instead of Deployment for stable network identity
- **PersistentVolume** ensures data survives pod restarts
- **Single replica** for simplicity (can be enhanced with replication)

### Grafana Monitoring

**Version**: Latest  
**Deployment**: Deployment in `monitoring` namespace  
**Purpose**: Visualize weather data and metrics

#### Features:
- Pre-configured PostgreSQL datasource
- Dashboard provisioning support
- Anonymous viewer access enabled
- Persistent storage for configurations

### Flux CD

**Version**: v2  
**Purpose**: GitOps continuous deployment  
**Components**:
- Source Controller: Monitors Git repositories
- Kustomize Controller: Applies Kustomize configurations
- Helm Controller: Manages Helm releases (future use)

---

## Data Flow

```
┌─────────────┐
│ WeatherAPI  │
│  .com API   │
└──────┬──────┘
       │ HTTP Request
       │ (every 5 min)
       ▼
┌─────────────────┐
│  Weather App    │
│   (Python)      │
│                 │
│ - Fetch data    │
│ - Update metrics│
│ - Store in DB   │
└────┬───────┬────┘
     │       │
     │       │ Metrics scrape
     │       ▼
     │  ┌──────────┐
     │  │Prometheus│
     │  │(metrics) │
     │  └────┬─────┘
     │       │
     │ SQL   │ Query
     │ INSERT│ metrics
     ▼       ▼
┌─────────────────┐      ┌─────────┐
│   PostgreSQL    │◄─────┤ Grafana │
│   (Database)    │ SQL  │ (Viz)   │
│                 │ Query└─────────┘
│ - weather_data  │
│   table         │
└─────────────────┘
```

---

## Security Architecture

### Defense in Depth

1. **Container Security**
   - Non-root user (UID 1000)
   - Read-only root filesystem where possible
   - Dropped all Linux capabilities
   - No privilege escalation

2. **Secret Management**
   - Kubernetes Secrets for sensitive data
   - Base64 encoding at rest
   - Can be enhanced with Sealed Secrets or external secret stores

3. **Network Security**
   - Service-to-service communication within cluster
   - Network policies can be added for micro-segmentation
   - Ingress with TLS termination (optional)

4. **Resource Limits**
   - CPU and memory limits prevent resource exhaustion
   - Pod disruption budgets for availability
   - Resource quotas at namespace level

### Secret Storage

Current approach: Kubernetes Secrets

**Production Recommendations**:
- Bitnami Sealed Secrets for encrypted secrets in Git
- HashiCorp Vault for dynamic secret generation
- Cloud provider secret managers (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager)
- External Secrets Operator for multi-cloud secret management

---

## Deployment Strategy

### GitOps Workflow

```
Developer ──┐
            ▼
       ┌─────────┐
       │   Git   │◄──── Flux CD (monitors)
       │  Repo   │
       └────┬────┘
            │
            ▼
    ┌──────────────┐
    │ Flux applies │
    │  manifests   │
    └──────┬───────┘
           │
           ▼
    ┌─────────────┐
    │ Kubernetes  │
    │   Cluster   │
    └─────────────┘
```

1. Developer pushes code to GitHub
2. GitHub Actions builds Docker image
3. Image pushed to Docker Hub
4. Developer updates manifest with new image tag
5. Flux detects change and applies to cluster
6. Kubernetes rolling update deploys new version

### Rolling Updates

- **Strategy**: RollingUpdate
- **Max Unavailable**: 0 (default)
- **Max Surge**: 1 (default)

Ensures zero-downtime deployments with graceful shutdown handling.

---

## Scalability Considerations

### Current State
- Single replica for weather app
- Single replica for PostgreSQL
- Single replica for Grafana

### Scaling Options

#### Horizontal Pod Autoscaling (HPA)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: weather-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: weather-app
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### Database Scaling
- **Read Replicas**: PostgreSQL streaming replication
- **Connection Pooling**: PgBouncer
- **High Availability**: Patroni or Stolon for automatic failover

---

## Observability Strategy

### Metrics (Prometheus)

**Application Metrics**:
- Request counts and error rates
- API response times (histogram)
- Database operation counters
- Current weather readings (gauges)

**Infrastructure Metrics** (via node-exporter):
- CPU, memory, disk usage
- Network I/O
- Pod resource consumption

### Logging

**Current**: Python logging to stdout  
**Future Enhancements**:
- Structured JSON logging
- Log aggregation (Loki, ELK, or cloud provider)
- Correlation IDs for request tracing
- Log levels configurable via environment

### Alerting

**Recommended AlertManager Rules**:
```yaml
- alert: WeatherAppDown
  expr: up{job="weather-app"} == 0
  for: 5m
  annotations:
    summary: "Weather app is down"

- alert: HighAPIErrorRate
  expr: rate(weather_api_errors_total[5m]) > 0.1
  for: 5m
  annotations:
    summary: "High API error rate detected"

- alert: DatabaseConnectionFailed
  expr: db_healthy == 0
  for: 2m
  annotations:
    summary: "Database connection failed"
```

---

## Future Enhancements

### Short Term
- [ ] Add unit and integration tests
- [ ] Create Grafana dashboard JSON
- [ ] Implement proper database migrations (Alembic)
- [ ] Add Helm chart for easier deployment

### Medium Term
- [ ] Multi-region weather collection
- [ ] Historical trend analysis
- [ ] API for weather data queries
- [ ] Email/SMS alerts for extreme weather

### Long Term
- [ ] Machine learning for weather predictions
- [ ] Multi-tenancy support
- [ ] Real-time streaming architecture (Kafka)
- [ ] Mobile app integration

---

## Technology Decisions

### Why Python?
- Quick prototyping
- Rich ecosystem for data processing
- Excellent PostgreSQL support
- Native Prometheus client library

### Why PostgreSQL?
- Proven reliability for time-series data
- ACID compliance
- Strong community support
- Excellent Grafana integration

### Why Flux CD?
- Kubernetes-native GitOps
- Supports Kustomize and Helm
- Active development and community
- Low resource overhead

### Why K3s?
- Lightweight Kubernetes for homelab
- Full K8s compatibility
- Easy installation
- Low resource requirements

---

## Performance Considerations

### Current Performance Profile
- **Weather App**: ~30MB memory, minimal CPU
- **PostgreSQL**: ~256MB memory, light CPU
- **Grafana**: ~128MB memory, light CPU

### Optimization Opportunities
1. **Database Connection Pooling**: Reduce connection overhead
2. **Caching**: Cache weather API responses (redis)
3. **Batch Inserts**: Batch multiple weather readings
4. **Index Optimization**: Add indexes on timestamp and city columns

---

## Disaster Recovery

### Backup Strategy (Recommended)

1. **PostgreSQL Backups**
   ```bash
   # Daily pg_dump to S3/NFS
   kubectl exec statefulset/postgres -- pg_dump -U postgres weather_db | \
     gzip > backup-$(date +%Y%m%d).sql.gz
   ```

2. **PVC Snapshots**
   - Use VolumeSnapshot API
   - Schedule automated snapshots

3. **GitOps Recovery**
   - All infrastructure in Git
   - Can recreate cluster from scratch
   - Only need to restore database data

### Recovery Time Objective (RTO)
- **Application**: < 5 minutes (redeploy from Git)
- **Database**: Depends on backup size (estimate: 15-30 min for 10GB)

### Recovery Point Objective (RPO)
- **Application**: 0 (stateless)
- **Database**: Depends on backup frequency (recommend: 1 hour)

---

## Compliance & Standards

### Standards Followed
- ✅ Kubernetes best practices
- ✅ 12-Factor App methodology
- ✅ OpenTelemetry compatibility (future)
- ✅ Prometheus naming conventions
- ✅ Semantic versioning for releases

### Security Standards
- ✅ CIS Kubernetes Benchmark (partial)
- ✅ OWASP Container Security
- ✅ Principle of least privilege

---

## Conclusion

This architecture balances simplicity with production-readiness, making it an excellent learning example while demonstrating real-world best practices. The modular design allows for easy enhancement and scaling as requirements grow.
