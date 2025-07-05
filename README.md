# Prom-Cache

A high-performance caching frontend server for Prometheus metrics endpoints. Prom-Cache acts as a proxy that fetches metrics from configured endpoints in the background and serves cached responses, reducing load on your metrics sources and improving query performance.

## Features

- **Background Fetching**: Continuously fetches metrics from configured endpoints in separate threads
- **Automatic Caching**: Serves cached responses to reduce load on source metrics endpoints
- **Auto-cleanup**: Automatically stops background jobs when responses haven't been accessed for 10 minutes
- **Error Handling**: Graceful handling of network errors and endpoint failures
- **Docker Support**: Ready-to-deploy Docker container
- **Fast API**: Built with shatter-api for high performance

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t prom-cache .

# Run the container
docker run -p 9221:9221 prom-cache
```

### Using Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  prom-cache:
    build: ghcr.io/ripplefcl/prom-cache:latest
    ports:
      - "9221:9221"
    restart: unless-stopped
```

Then run:

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f prom-cache

# Stop the service
docker-compose down
```

### Local Development

1. **Install dependencies** (requires Python 3.13+):
   ```bash
   pip install poetry
   poetry install
   ```

2. **Run the server**:
   ```bash
   poetry run uvicorn server.main:app --interface wsgi --host 0.0.0.0 --port 9221
   ```

## Usage

### Fetching Metrics

Send a GET request to `/metrics` with the source endpoint as a query parameter:

```bash
# Fetch metrics from a Prometheus endpoint
curl "http://localhost:9221/metrics?endpoint=http://your-service:9090/metrics"

# Pass additional query parameters to the source endpoint
curl "http://localhost:9221/metrics?endpoint=http://your-service:9090/metrics&job=my-job&instance=server1"
```

### Prometheus Configuration

To use prom-cache with Prometheus, configure your `prometheus.yml` with relabeling to add the endpoint parameter:

```yaml
scrape_configs:
  - job_name: 'prom-cache'
    static_configs:
      - targets: ['my-exporter:9999']
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_endpoint
      - target_label: __address__
        replacement: "prom-cache:9221"
```

### API Endpoint

**GET /metrics**

Query Parameters:
- `endpoint` (required): The URL of the source metrics endpoint to fetch from
- Additional parameters: All other query parameters are forwarded to the source endpoint

Response:
- **200 OK**: Returns the cached metrics in Prometheus text format
- **404 Not Found**: When the source endpoint is unreachable or returns an error

## How It Works

1. **Request Processing**: When you make a request to `/metrics`, prom-cache checks if there's already a background job fetching from the specified endpoint
2. **Background Jobs**: If no job exists (or the previous one stopped), a new background thread is started to continuously fetch metrics from the source
3. **Caching**: The background job fetches metrics every second and caches the latest response
4. **Serving**: Requests are served from the cache immediately, providing fast response times
5. **Cleanup**: Background jobs automatically stop if no requests are made for 10 minutes


## Use Cases

- **Prometheus Federation**: Cache metrics from multiple Prometheus instances
- **Load Reduction**: Reduce load on slow or resource-constrained metrics endpoints
- **Performance Optimization**: Improve dashboard and alerting performance by serving cached metrics
- **Metrics Aggregation**: Centralize access to distributed metrics endpoints

