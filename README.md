# Automated Ephemeral File Sharing Portal

An automated, ephemeral file-sharing portal designed to run on a home server (e.g., ZimaOS). It exposes files from an external HDD, allows memory-efficient 10GB+ streaming uploads to GoFile.io, and automatically cleans up files older than 24 hours.

## Deployment with Docker Compose (ZimaOS / Home Server)

1. Create a `.env` file in the root directory (or rename `.env.example` if available) and add your environment variables:
   ```env
   GOFILE_API_TOKEN=your_token_here
   SHARED_DIR=./test_files
   ```
2. Modify the `docker-compose.yml` file to map your server's external HDD to the container's volume (default is `/mnt/external_hdd:/app/test_files`).
3. Build and start the container in detached mode:
   ```bash
   docker-compose up -d --build
   ```
4. Access the portal at `http://<your-server-ip>:8000`.