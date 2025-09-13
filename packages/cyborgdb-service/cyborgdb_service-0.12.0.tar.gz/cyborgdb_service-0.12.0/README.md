# CyborgDB Service

![PyPI - Version](https://img.shields.io/pypi/v/cyborgdb_service)
![PyPI - License](https://img.shields.io/pypi/l/cyborgdb_service)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cyborgdb_service)

A FastAPI-based REST API wrapper for [CyborgDB](https://docs.cyborg.co), providing Confidential Vector DB capabilities over HTTP. It enables you to ingest & search vectors embeddings in a privacy-preserving manner, without revealing the contents of the vectors themselves. CyborgDB works with existing DBs (e.g., Postgres, Redis) and enables you to add, query and retrieve vector embeddings with transparent end-to-end encryption.

## Features

- **End-to-End Encryption**: Vector embeddings remain encrypted throughout their lifecycle, including at search time
- **Zero-Trust Design**: Novel architecture keeps confidential inference data secure
- **High Performance**: GPU-accelerated indexing and retrieval with CUDA support
- **Familiar API**: Easy integration with existing AI workflows
- **Multiple Backing Stores**: Works with PostgreSQL, Redis, and in-memory storage
- **Cloud Ready**: Supports AWS RDS, AWS ElastiCache, Azure Database for PostgreSQL, Azure Cache for Redis, Google Cloud SQL, and Google Cloud Memorystore

## Getting Started

To get started in minutes, check out our [Quickstart Guide](https://docs.cyborg.co/quickstart).

### Installation

1. Install `cyborgdb-service`
```bash
# Install the CyborgDB Service
pip install cyborgdb-service
```

2. Set environment variables
```bash
export CYBORGDB_API_KEY=your_api_key_here
export CYBORGDB_DB_TYPE='redis|postgres'
export CYBORGDB_CONNECTION_STRING=your_connection_string_here
```

For connection string examples run `cyborgdb-service --help`

2. Run the server

```bash
cyborgdb-service
```

### API Key Configuration

You need to provide your API key using **any** of these methods:

#### Method 1: Environment Variable (Easiest)

```bash
export CYBORGDB_API_KEY=your_api_key_here
cyborgdb-service
```

#### Method 2: .env File

Create a `.env` file in the project root:
```
CYBORGDB_API_KEY=your_api_key_here
```
Then run:
```bash
cyborgdb-service
```

#### Method 3: Inline with Launch
```bash
CYBORGDB_API_KEY=your_api_key_here cyborgdb-service
```



## Documentation

For more information on CyborgDB, see the [Cyborg Docs](https://docs.cyborg.co).

## License

CyborgDB Service is licensed under the MIT License. The underlying library, CyborgDB Core, is licensed under Cyborg's [Terms of Service](https://www.cyborg.co/terms-of-service).