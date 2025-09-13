# CyborgDB Service

![Docker Image Size](https://img.shields.io/docker/image-size/cyborginc/cyborgdb-service/latest)
![Docker Pulls](https://img.shields.io/docker/pulls/cyborginc/cyborgdb-service)

A FastAPI-based REST API wrapper for [CyborgDB](https://www.cyborg.co), providing Confidential Vector DB capabilities over HTTP. It enables you to ingest & search vectors embeddings in a privacy-preserving manner, without revealing the contents of the vectors themselves. CyborgDB works with existing DBs (e.g., Postgres, Redis) and enables you to add, query and retrieve vector embeddings with transparent end-to-end encryption.

## Features

- **End-to-End Encryption**: Vector embeddings remain encrypted throughout their lifecycle, including at search time
- **Zero-Trust Design**: Novel architecture keeps confidential inference data secure
- **High Performance**: GPU-accelerated indexing and retrieval with CUDA support
- **Familiar API**: Easy integration with existing AI workflows
- **Multiple Backing Stores**: Works with PostgreSQL, Redis, and in-memory storage
- **Cloud Ready**: Supports AWS RDS, AWS ElastiCache, Azure Database for PostgreSQL, Azure Cache for Redis, Google Cloud SQL, and Google Cloud Memorystore

## Quick Start

### Linux
```bash
sudo docker run -it --network host \
  -e CYBORGDB_DB_TYPE=postgres \
  -e "CYBORGDB_CONNECTION_STRING=host=localhost port=5432 dbname=postgres user=postgres password=your_password" \
  -e CYBORGDB_API_KEY=cyborg_your_api_key_here \
  cyborginc/cyborgdb-service:latest
```

### macOS
```bash
sudo docker run -it -p 8000:8000 \
  -e CYBORGDB_DB_TYPE=postgres \
  -e 'CYBORGDB_CONNECTION_STRING=host=host.docker.internal port=5432 dbname=postgres user=postgres password=your_password' \
  -e CYBORGDB_API_KEY=cyborg_your_api_key_here \
  cyborginc/cyborgdb-service:latest
```

### With Redis (Linux)
```bash
sudo docker run -it --network host \
  -e CYBORGDB_DB_TYPE=redis \
  -e "CYBORGDB_CONNECTION_STRING=host=localhost,port=6379,db=0" \
  -e CYBORGDB_API_KEY=cyborg_your_api_key_here \
  cyborginc/cyborgdb-service:latest
```

### With Redis (macOS)
```bash
sudo docker run -it -p 8000:8000 \
  -e CYBORGDB_DB_TYPE=redis \
  -e 'CYBORGDB_CONNECTION_STRING=host=host.docker.internal,port=6379,db=0' \
  -e CYBORGDB_API_KEY=cyborg_your_api_key_here \
  cyborginc/cyborgdb-service:latest
```

## Multi-Architecture Support

This image supports multiple architectures and will automatically pull the correct one for your system:

| Architecture | Status | Use Case |
|--------------|--------|----------|
| `linux/amd64` | ✅ Supported | Intel/AMD servers, most cloud instances |
| `linux/arm64` | ✅ Supported | Apple Silicon Macs, ARM servers, Raspberry Pi 4+ |

## Docker Compose

### With PostgreSQL
```yaml
version: '3.8'
services:
  cyborgdb:
    image: cyborginc/cyborgdb-service:latest
    ports:
      - "8000:8000"
    environment:
      - CYBORGDB_DB_TYPE=postgres
      - CYBORGDB_CONNECTION_STRING=host=postgres port=5432 dbname=cyborgdb user=cyborgdb password=secure_password
      - CYBORGDB_API_KEY=cyborg_your_api_key_here
    depends_on:
      - postgres
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=cyborgdb
      - POSTGRES_USER=cyborgdb
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### With Redis
```yaml
version: '3.8'
services:
  cyborgdb:
    image: cyborginc/cyborgdb-service:latest
    ports:
      - "8000:8000"
    environment:
      - CYBORGDB_DB_TYPE=redis
      - CYBORGDB_CONNECTION_STRING=host=redis,port=6379,db=0
      - CYBORGDB_API_KEY=cyborg_your_api_key_here
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `CYBORGDB_API_KEY` | Your CyborgDB API key | ✅ | `cyborg_abc123...` |
| `CYBORGDB_DB_TYPE` | Database type | ✅ | `postgres` or `redis` |
| `CYBORGDB_CONNECTION_STRING` | Database connection string | ✅ | See examples above |
| `CYBORGDB_VERSION` | Service version | ❌ | `0.11.2` |

## Database Support

### PostgreSQL
- **Connection String Format**: `host=hostname port=5432 dbname=database user=username password=password`
- **Recommended for**: Production workloads, complex queries, ACID compliance
- **Performance**: Excellent for structured data and complex relationships

### Redis
- **Connection String Format**: `host=hostname,port=6379,db=0`
- **Recommended for**: High-speed caching, simple key-value operations
- **Performance**: Ultra-fast for read-heavy workloads

## Platform Differences

### Why Different Commands?

**Linux**: Uses `--network host` because Docker on Linux runs natively and can directly access the host network.

**macOS**: Uses `-p 8000:8000` and `host.docker.internal` because Docker runs in a lightweight VM and needs port mapping to communicate with the host.

## Health Check

Once running, verify the service:
```bash
curl http://localhost:8000/v1/health
```

Access the API documentation at: http://localhost:8000/docs

## Image Details

- **Base Image**: `continuumio/miniconda3:latest`
- **Python Version**: 3.12
- **PyTorch**: CPU-optimized for maximum compatibility
- **Size**: ~1.8GB (AMD64), ~1.9GB (ARM64)
- **Platforms**: `linux/amd64`, `linux/arm64`

## Getting API Keys

Visit [CyborgDB](https://cyborgdb.com) to sign up and get your API key.

## Source Code

GitHub: [cyborginc/cyborgdb-service](https://github.com/cyborginc/cyborgdb-service)