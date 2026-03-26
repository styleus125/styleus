# DLO E-Commerce — VPS Deployment Guide

## Prerequisites
- VPS running Ubuntu 20.04+ or Debian 11+
- Port 80 and 443 open in your VPS firewall
- A domain name pointed to your VPS IP (for SSL)
- At least 1GB RAM recommended

---

## 1. Connect to your VPS

```bash
ssh root@your-vps-ip
```

---

## 2. Install Docker & Docker Compose

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Verify installation
docker --version
docker compose version
```

---

## 3. Transfer Project Files

**Option A — Copy from local machine:**
```bash
scp -r /Users/nabeel/work/ai-work/dlo root@your-vps-ip:/opt/dlo
```

**Option B — Clone from GitHub:**
```bash
git clone https://github.com/your-repo/dlo.git /opt/dlo
```

---

## 4. Configure Environment

```bash
cd /opt/dlo

# Create .env file with real values
cat > .env << EOF
SECRET_KEY=change-this-to-a-long-random-string
STRIPE_PUBLIC_KEY=pk_live_your_real_key
STRIPE_SECRET_KEY=sk_live_your_real_key
EOF
```

Update `docker-compose.yml` to use the `.env` file:

```yaml
services:
  web:
    build: .
    container_name: dlo_app
    ports:
      - "8080:5000"
    env_file:
      - .env
    environment:
      - DATABASE_URL=sqlite:////app/data/dlo.db
    volumes:
      - dlo_data:/app/data
      - dlo_uploads:/app/static/uploads
    restart: unless-stopped

volumes:
  dlo_data:
  dlo_uploads:
```

---

## 5. Build and Launch

```bash
cd /opt/dlo
docker compose up --build -d

# Verify it's running
docker compose ps
docker compose logs -f
```

App will be available at `http://your-vps-ip:8080`

**Admin login:** `admin@dlo.com` / `admin123`

---

## 6. Set Up Nginx Reverse Proxy (Recommended)

```bash
apt install nginx -y
```

Create a config file:

```bash
nano /etc/nginx/sites-available/dlo
```

Paste the following (replace `yourdomain.com`):

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable and restart Nginx:

```bash
ln -s /etc/nginx/sites-available/dlo /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

---

## 7. Enable HTTPS with SSL (Recommended)

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Your site will be live at `https://yourdomain.com`

---

## Management Commands

```bash
# View live logs
docker compose -f /opt/dlo/docker-compose.yml logs -f

# Restart app
docker compose -f /opt/dlo/docker-compose.yml restart

# Update app after code changes
cd /opt/dlo && git pull && docker compose up --build -d

# Stop app
docker compose -f /opt/dlo/docker-compose.yml down
```
