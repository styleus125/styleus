#!/bin/bash
# Run this ONCE on the VPS to bootstrap the first SSL certificate.
# After this, certbot auto-renews every 12h via the certbot container.

set -e

DOMAIN="aibrainlabs.online"
EMAIL="your-email@example.com"   # <-- change this

echo "### Starting containers with HTTP-only config (certs don't exist yet)..."

# Temporarily use a plain HTTP-only nginx config so nginx can start
# without the SSL certs that don't exist yet.
cat > ./nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name aibrainlabs.online www.aibrainlabs.online;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
EOF

docker compose up -d nginx web

echo "### Requesting Let's Encrypt certificate..."
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

echo "### Restoring full HTTPS nginx config..."
cat > ./nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name aibrainlabs.online www.aibrainlabs.online;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name aibrainlabs.online www.aibrainlabs.online;

    ssl_certificate     /etc/letsencrypt/live/aibrainlabs.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aibrainlabs.online/privkey.pem;

    ssl_protocols             TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache         shared:SSL:10m;
    ssl_session_timeout       1d;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options    nosniff;
    add_header X-Frame-Options           DENY;
    add_header X-XSS-Protection          "1; mode=block";

    client_max_body_size 20M;

    location / {
        proxy_pass         http://web:5000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
EOF

echo "### Reloading nginx with HTTPS config..."
docker compose exec nginx nginx -s reload

echo "### Starting certbot auto-renew container..."
docker compose up -d certbot

echo ""
echo "Done! Your site is live at https://$DOMAIN"
