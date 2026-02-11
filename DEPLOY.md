# Deploying Table Talks to a NAS

You need the Docker image and a `.env` file (with `BOT_TOKEN`) on the NAS. Three ways to get the image there:

---

## Option 1: Push to a registry (best for updates)

**On your computer**

1. Tag the image for your registry (replace `YOUR_USER` with Docker Hub username or your registry host):

   ```bash
   make docker-build
   docker tag table-talks:latest YOUR_USER/table-talks:latest
   docker push YOUR_USER/table-talks:latest
   ```

2. Copy `.env` to the NAS (create it there with your `BOT_TOKEN`).

**On the NAS**

1. Log in if using a private registry: `docker login`
2. Pull and run:

   ```bash
   docker pull YOUR_USER/table-talks:latest
   docker run -d --restart unless-stopped --env-file .env -p 9999:9999 --name table-talks YOUR_USER/table-talks:latest
   ```

   Or with Compose: put `image: YOUR_USER/table-talks:latest` in `docker-compose.yml` (and remove or comment out `build: .`), then:

   ```bash
   docker compose up -d
   ```

---

## Option 2: Save image and copy (no registry)

**On your computer**

```bash
make docker-build
docker save table-talks:latest | gzip > table-talks.tar.gz
# Copy table-talks.tar.gz and .env to the NAS (scp, USB, Synology File Station, etc.)
```

**On the NAS**

```bash
docker load < table-talks.tar.gz
# Create .env with BOT_TOKEN=...
docker run -d --restart unless-stopped --env-file .env -p 9999:9999 --name table-talks table-talks:latest
```

Or copy `docker-compose.yml` and run (use `--no-build` so Compose uses the loaded image):

```bash
docker load < table-talks.tar.gz
docker compose up -d --no-build
```

---

## Option 3: Build on the NAS

**On your computer**

- Copy the project to the NAS (git clone, rsync, or copy the folder). Example with rsync:

  ```bash
  rsync -av --exclude .venv --exclude .git ./ user@NAS_IP:/path/on/nas/table-talks/
  ```

**On the NAS**

```bash
cd /path/on/nas/table-talks
# Create .env with BOT_TOKEN=...
docker compose up -d --build
# or: make docker-build && make docker-run (run in foreground; add -d and --restart for background)
```

---

## After deploy

- **Health check:** `http://NAS_IP:9999/health` should return 200.
- **Logs:** `docker logs -f table-talks`
- **Stop:** `docker stop table-talks` or `docker compose down`

Ensure port 9999 is allowed on the NAS firewall if you want to reach the health endpoint from another machine.
