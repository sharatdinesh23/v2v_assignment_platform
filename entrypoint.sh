#!/bin/sh

# Start the Reflex backend in the background on port 8000
reflex run --env prod --backend-only --loglevel info &

# Start Caddy in the foreground
caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
