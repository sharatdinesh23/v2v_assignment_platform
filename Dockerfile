# Stage 1: Build the Reflex static frontend
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies for building Node/npm
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required by Reflex to compile Next.js static files)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Export frontend static assets to .web/build/client
# Reflex requires an API_URL at export time so the client browser knows where to send requests.
ARG API_URL
ENV API_URL=$API_URL
RUN reflex export --frontend-only --no-zip

# Stage 2: Runtime image
FROM python:3.12-slim

# Install Caddy
RUN apt-get update && apt-get install -y \
    curl \
    debian-keyring \
    debian-archive-keyring \
    apt-transport-https \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list \
    && apt-get update \
    && apt-get install -y caddy \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Copy the statically compiled frontend from the builder stage
COPY --from=builder /app/.web/build/client /srv

# Copy Caddyfile and entrypoint script
COPY Caddyfile /etc/caddy/Caddyfile
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose HTTP and HTTPS ports
EXPOSE 80 443

ENTRYPOINT ["/entrypoint.sh"]
