# ProPublica MCP Server

A Model Context Protocol (MCP) server that provides access to ProPublica's Nonprofit Explorer API, enabling AI models to search and analyze nonprofit organizations' Form 990 data for CRM integration and prospect research.

> **🚨 Breaking Changes in v1.0.0**
> 
> Version 1.0.0 introduces **breaking changes** with the implementation of MCP 2025-03-26 Streamable HTTP transport:
> - **Remote deployments** now use a single `/` endpoint instead of `/sse` and `/messages`  
> - **MCP client configuration** has changed for cloud deployments (see Usage section below)
> - **Improved compatibility** with Claude Desktop, Cursor, and other MCP clients
> - **Backwards incompatible** with MCP clients expecting the old SSE transport

## Features

- Search nonprofit organizations by name, location, and category
- Retrieve detailed organization profiles and contact information
- Access Form 990 financial data and filing history
- Analyze financial trends across multiple years
- Export data in CRM-ready formats
- Built with FastMCP for optimal performance

## 🚀 One-Click Deployment

Deploy the ProPublica MCP server instantly to your preferred cloud platform:

### DigitalOcean App Platform
[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/asachs01/propublica-mcp/tree/deploy)

### Cloudflare Workers
[![Deploy to Cloudflare Workers](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/asachs01/propublica-mcp/tree/deploy)

Both platforms offer:
- **DigitalOcean**: Container-based deployment with automatic scaling and monitoring
- **Cloudflare**: Serverless deployment with global edge distribution and zero cold starts

## Quick Start

### Prerequisites

- Compatible MCP client (Claude Desktop, Cursor, etc.)
- For development: Python 3.8 or higher, Git

### Installation

#### Option 1: DXT Extension (Recommended)

The easiest way to install the ProPublica MCP server is using the DXT extension format:

**Install from GitHub Releases:**
1. Go to the [releases page](https://github.com/asachs01/propublica-mcp/releases)
2. Download the latest `propublica-mcp-[version].dxt` file
3. Install the DXT extension:

**For Claude Desktop:**
```bash
# Install from downloaded file
claude-desktop install propublica-mcp-[version].dxt

# Or install directly from GitHub release
claude-desktop install https://github.com/asachs01/propublica-mcp/releases/latest/download/propublica-mcp.dxt
```

**For other MCP clients:**
Follow your client's DXT installation instructions or extract the DXT file to your MCP extensions directory.

#### Option 2: Docker (Production)

For production deployments or containerized environments:

**Quick Start with Docker:**
```bash
# Pull the latest image from GitHub Container Registry
docker pull ghcr.io/asachs01/propublica-mcp:latest

# Run the server
docker run -it --rm ghcr.io/asachs01/propublica-mcp:latest
```

**Using Docker Compose:**
1. Download the compose file:
```bash
curl -O https://raw.githubusercontent.com/asachs01/propublica-mcp/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/asachs01/propublica-mcp/main/env.example
```

2. Configure environment (optional):
```bash
cp env.example .env
# Edit .env file with your preferred settings
```

3. Start the service:
```bash
docker-compose up -d
```

#### Option 3: Cloud Deployment

**DigitalOcean App Platform:**
1. Click the "Deploy to DO" button above
2. Connect your GitHub account (if not already connected)
3. Configure environment variables (optional - defaults are provided)
4. Click "Deploy" - your app will be live in minutes with a public URL

**Cloudflare Workers:**
1. Click the "Deploy to Cloudflare Workers" button above
2. Connect your GitHub account and authorize Cloudflare
3. Configure any environment variables as needed
4. Deploy - your serverless function will be live globally

> **🚀 Production Deployment Strategy**
> 
> Cloud deployments only deploy from the **`deploy`** branch, which contains stable, tested releases:
> - **Development**: All work happens on `main` branch
> - **Releases**: When tags are created (e.g., `v0.2.0`), the `deploy` branch is automatically updated
> - **Cloud Platforms**: DigitalOcean and Cloudflare deploy only from the `deploy` branch
> - **Benefits**: Ensures only stable, released versions reach production environments

#### Option 4: Local Python Installation (Development)

For development and customization:

1. Clone the repository:
```bash
git clone https://github.com/asachs01/propublica-mcp.git
cd propublica-mcp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package:
```bash
pip install -e .
```

5. Run the server:

**For stdio mode (local MCP clients):**
```bash
python -m propublica_mcp.server
```

**For HTTP mode (remote MCP clients):**
```bash
python -m propublica_mcp.server --http --host 0.0.0.0 --port 8080
```

**Available options:**
- `--http`: Enable HTTP server mode for remote MCP clients
- `--host`: Host to bind to (default: 127.0.0.1)
- `--port`: Port to bind to (default: 8080)
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR)

### Usage with MCP Clients

This server implements the **MCP 2025-03-26 Streamable HTTP** transport protocol and can be used with any MCP client, including Claude Desktop, Cursor, and other compatible tools.

#### For DXT Extension (Recommended):

Once installed as a DXT extension, the server will be automatically configured. Most MCP clients will detect and load the extension automatically.

**Manual DXT Configuration (if needed):**
```json
{
  "mcpServers": {
    "propublica-mcp": {
      "extension": "propublica-mcp.dxt",
      "description": "ProPublica Nonprofit Explorer MCP Server (DXT Extension)"
    }
  }
}
```

#### For Cloud Deployment (Remote MCP Server):
**DigitalOcean/Cloudflare (Streamable HTTP):**

For remote Python MCP servers, you'll need to use an HTTP transport. Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "propublica-mcp": {
      "transport": {
        "type": "http",
        "url": "https://propublica-mcp-lk97f.ondigitalocean.app"
      },
      "description": "ProPublica Nonprofit Explorer MCP Server (Remote)"
    }
  }
}
```

#### For Local Installation (stdio transport):
```json
{
  "mcpServers": {
    "propublica-mcp": {
      "command": "python",
      "args": ["-m", "propublica_mcp.server"],
      "cwd": "/path/to/propublica-mcp",
      "env": {}
    }
  }
}
```

#### For Docker Deployment (stdio transport):
```json
{
  "mcpServers": {
    "propublica-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "ghcr.io/asachs01/propublica-mcp:latest"
      ],
      "description": "ProPublica Nonprofit Explorer MCP Server"
    }
  }
}
```

#### For Local HTTP Server (development):
```bash
# Start HTTP server locally
python -m propublica_mcp.server --http --host 0.0.0.0 --port 8080
```

Then configure as remote server:
```json
{
  "mcpServers": {
    "propublica-mcp": {
      "transport": {
        "type": "http",
        "url": "http://localhost:8080"
      },
      "description": "ProPublica Nonprofit Explorer MCP Server (Local HTTP)"
    }
  }
}
```

## API Tools

### Core Tools

- **search_nonprofits**: Search for nonprofit organizations
- **get_organization**: Get detailed organization information by EIN
- **get_organization_filings**: Retrieve Form 990 filings for an organization

### Advanced Tools

- **analyze_nonprofit_financials**: Analyze financial trends across multiple years
- **search_similar_nonprofits**: Find similar organizations
- **export_nonprofit_data**: Format data for CRM import

## Data Sources

This server uses the [ProPublica Nonprofit Explorer API](https://projects.propublica.org/nonprofits/api) which provides:

- IRS Form 990 data for tax-exempt organizations
- Organization profiles and contact information
- Financial data and filing history
- NTEE categorization and 501(c) status

## Development

### Project Structure

```
propublica-mcp/
├── server/                    # DXT extension structure
│   ├── src/
│   │   └── propublica_mcp/
│   │       ├── __init__.py
│   │       ├── server.py
│   │       ├── api_client.py
│   │       ├── models.py
│   │       └── tools/
│   ├── requirements.txt
│   └── manifest.json         # DXT extension manifest
├── src/                      # Legacy source structure (for compatibility)
│   └── propublica_mcp/
├── tests/
├── config/
├── .github/
│   └── workflows/
│       └── build-dxt.yml     # Automated DXT packaging
├── Dockerfile
├── docker-compose.yml
├── env.example
├── requirements.txt
├── manifest.json             # Root DXT manifest
└── README.md
```

The project now supports both the traditional Python package structure and the new DXT extension format. The `server/` directory contains the DXT-compatible structure that gets packaged into `.dxt` files during releases.

### Development with Docker

#### Building the Docker Image

```bash
# Build the image
docker build -t propublica-mcp:dev .

# Or use docker-compose
docker-compose build
```

#### Running Development Environment

```bash
# Run with docker-compose (includes volume mounts for development)
docker-compose -f docker-compose.yml -f docker-compose.override.yml up

# Run tests in container
docker run --rm -v $(pwd):/app propublica-mcp:dev pytest tests/ -v
```

#### Environment Variables

The Docker container supports these environment variables:

- `LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `API_RATE_LIMIT`: Requests per minute (default: 60)
- `PROPUBLICA_API_BASE_URL`: API base URL (rarely needs changing)

### Running Tests

#### Local Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src/propublica_mcp
```

#### Docker Testing

```bash
# Run tests in Docker
docker run --rm ghcr.io/asachs01/propublica-mcp:latest \
  python -m pytest tests/ -v

# Or with docker compose
docker compose run --rm propublica-mcp pytest tests/ -v
```

### Building DXT Extensions

The project includes automated DXT packaging via GitHub Actions. DXT files are automatically built and attached to releases.

#### Automated DXT Building (Recommended)

Create a tag to trigger automated DXT packaging:

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0
```

This will:
1. Package the `server/` directory into a `.dxt` file
2. Create a GitHub release with the DXT file attached
3. Build and publish Docker images to GitHub Container Registry

#### Manual DXT Building

For development or testing:

```bash
# Create DXT package manually
cd server/
zip -r ../propublica-mcp-dev.dxt .
```

### Publishing to GitHub Container Registry

The project includes automated publishing via GitHub Actions, but you can also publish manually:

#### Prerequisites

1. **GitHub Personal Access Token** with `packages:write` scope
2. **Authentication to GitHub Container Registry**:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
   ```

#### Automated Publishing (Recommended)

Push to the `main` branch or create a tag to trigger automated builds:

```bash
# Trigger build for main branch
git push origin main

# Create and push a version tag (also builds DXT)
git tag v1.0.0
git push origin v1.0.0
```

#### Manual Publishing

Use the provided script (requires local setup):

```bash
# Build and publish latest
./scripts/docker-publish.sh

# Build and publish specific version
./scripts/docker-publish.sh v1.0.0
```

#### Available Packages

Once published, the following packages will be available:

**DXT Extensions:**
- **Latest**: Available from [GitHub releases](https://github.com/asachs01/propublica-mcp/releases/latest)
- **Tagged versions**: `propublica-mcp-v1.0.0.dxt`
- **Direct download**: `https://github.com/asachs01/propublica-mcp/releases/latest/download/propublica-mcp.dxt`

**Docker Images:**
- **Latest**: `ghcr.io/asachs01/propublica-mcp:latest`
- **Tagged versions**: `ghcr.io/asachs01/propublica-mcp:v1.0.0`
- **Branch builds**: `ghcr.io/asachs01/propublica-mcp:main`

### Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check the documentation
- Review existing GitHub issues
- Create a new issue with detailed information 
