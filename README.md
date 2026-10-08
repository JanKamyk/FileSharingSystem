# Ephemeral File Sharing Portal

A universal, production-ready self-hosted server solution for ephemeral file sharing. This project provides a memory-efficient, asynchronous API built with FastAPI that is capable of streaming massive files (10GB+) directly to GoFile without overwhelming local RAM.

## Tech Stack

* **Python**: Core programming language.
* **FastAPI**: High-performance asynchronous web framework for building the API.
* **Docker & Docker Compose**: Containerization for seamless deployment.
* **httpx (async)**: For memory-efficient, chunked asynchronous streaming.
* **TailwindCSS**: Utility-first CSS framework (via CDN) for modern, responsive UI styling.

## Key Features

* **Multi-root Directory Browsing**: Seamlessly browse and serve files from multiple directories configured across your server.
* **Chunked Streaming Uploads**: Memory-efficient streaming of large files directly to external APIs like GoFile, bypassing the need to load the entire file into RAM.
* **Strict Path Traversal Protection**: Security-first approach utilizing robust path validation to prevent unauthorized directory access.
* **Automatic Public Links**: Automatically generates public download links via the GoFile API upon successful upload.

## Prerequisites

To run this application, ensure you have the following installed on your host system:

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)
* A [GoFile API Token](https://gofile.io/api)

## Configuration

The application is configured using environment variables. Create a `.env` file in the root directory of the project.

You must explicitly define the `SHARED_DIRS` variable as a JSON-formatted string mapping display names to their corresponding internal container paths.

Example `.env` file:

```env
# Your GoFile API token for uploading files
GOFILE_API_TOKEN=your_gofile_api_token_here

# JSON string mapping directory display names to internal container paths
SHARED_DIRS={"Movies": "./app/movies", "Music": "./app/music"}
```

## Deployment

Deploying the application is straightforward using Docker Compose.

1. Clone the repository to your self-hosted server.
2. Create and configure your `.env` file as shown in the Configuration section.
3. Ensure your `docker-compose.yml` is configured with the correct volume mappings for your server's storage.
4. Run the following command to build and start the container in detached mode:

```bash
docker-compose up -d --build
```

The portal will be accessible at `http://<your-server-ip>:8000`.