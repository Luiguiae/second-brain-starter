#!/usr/bin/env bash
# T32 (docs/tasks.md, Fase 9): smoke test post-deploy.
#
# Contra la URL pública de un deploy real (Koyeb u otro), verifica:
#   1. GET /health responde 200.
#   2. POST /diagnose con un caso feliz devuelve 200 y un archetype válido.
#   3. POST /mcp responde al handshake `initialize` del protocolo MCP.
#
# Uso:
#   ./scripts/smoke_test.sh https://tu-app.koyeb.app
# o:
#   BASE_URL=https://tu-app.koyeb.app ./scripts/smoke_test.sh
#
# Requiere: curl, python3 (para parsear JSON sin depender de jq).

set -euo pipefail

BASE_URL="${1:-${BASE_URL:-}}"
if [[ -z "$BASE_URL" ]]; then
  echo "Uso: $0 <base-url>  (o exportá BASE_URL=...)" >&2
  exit 2
fi
BASE_URL="${BASE_URL%/}"

fail=0

echo "== 1/3: GET /health =="
health_status=$(curl -s -o /tmp/smoke_health.json -w "%{http_code}" "$BASE_URL/health")
if [[ "$health_status" == "200" ]]; then
  echo "OK ($health_status): $(cat /tmp/smoke_health.json)"
else
  echo "FALLÓ: esperaba 200, llegó $health_status"
  fail=1
fi

echo
echo "== 2/3: POST /diagnose (caso feliz) =="
diagnose_status=$(curl -s -o /tmp/smoke_diagnose.json -w "%{http_code}" \
  -X POST "$BASE_URL/diagnose" \
  -H "Content-Type: application/json" \
  -d '{
    "purpose": "execute_projects",
    "maintenance_tolerance": "medium",
    "agent_usage": "already_using",
    "capture_volume": "daily_moderate",
    "technical_profile": "markdown_git_comfortable"
  }')
if [[ "$diagnose_status" == "200" ]]; then
  archetype=$(python3 -c "import json; print(json.load(open('/tmp/smoke_diagnose.json'))['archetype'])" 2>/dev/null || echo "?")
  echo "OK ($diagnose_status): archetype=$archetype"
  if [[ "$archetype" != "hybrid" ]]; then
    echo "FALLÓ: esperaba archetype=hybrid para este input, llegó '$archetype'"
    fail=1
  fi
else
  echo "FALLÓ: esperaba 200, llegó $diagnose_status"
  cat /tmp/smoke_diagnose.json
  fail=1
fi

echo
echo "== 3/3: POST /mcp (handshake initialize) =="
mcp_status=$(curl -s -o /tmp/smoke_mcp.txt -w "%{http_code}" \
  -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {},
      "clientInfo": {"name": "smoke-test", "version": "0.0.1"}
    }
  }')
if [[ "$mcp_status" == "200" ]] && grep -q "second-brain-starter" /tmp/smoke_mcp.txt; then
  echo "OK ($mcp_status): servidor MCP respondió al handshake"
else
  echo "FALLÓ: esperaba 200 con 'second-brain-starter' en el body, llegó $mcp_status"
  cat /tmp/smoke_mcp.txt
  fail=1
fi

rm -f /tmp/smoke_health.json /tmp/smoke_diagnose.json /tmp/smoke_mcp.txt

echo
if [[ "$fail" == "0" ]]; then
  echo "✅ Los 3 checks pasaron contra $BASE_URL"
else
  echo "❌ Al menos un check falló contra $BASE_URL"
  exit 1
fi
