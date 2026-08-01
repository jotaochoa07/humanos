#!/bin/bash
# Supabase Health Check - Pings database to prevent inactivity timeout
# Created: 2026-07-10
# Runs every hour via cronjob to keep Supabase connection alive

LOG_FILE="/c/Users/Jota Ochoa/Antigravity/02_Projects/humanos/supabase-ping.log"
PROJECT_ID="nuswdrztixelsfkccfqc"
ORG_ID="agente-jota"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Starting Supabase health check ==="

# Read credentials from .env
export $(grep -v '^#' /c/Users/Jota\ Ochoa/Antigravity/02_Projects/humanos/.env | xargs)

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    log "❌ ERROR: Missing SUPABASE_URL or SUPABASE_KEY in .env"
    exit 1
fi

log "✓ Credentials loaded"

# Ping Supabase API (GET a public endpoint to keep connection warm)
PING_URL="${SUPABASE_URL}/rest/v1/?select=1"

log "📍 Pinging: $PING_URL"

RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$PING_URL" \
    -H "apikey: $SUPABASE_KEY" \
    -H "Authorization: Bearer $SUPABASE_KEY" \
    -H "Content-Type: application/json" \
    -m 10)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

log "HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    log "✓ PING SUCCESS: Supabase is active"
    log "✓ Project: $PROJECT_ID | Organization: $ORG_ID"
    exit 0
else
    log "❌ PING FAILED: HTTP $HTTP_CODE"
    log "Response: $BODY"
    exit 1
fi
