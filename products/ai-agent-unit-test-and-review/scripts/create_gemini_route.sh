export ADMIN_API=http://localhost:9180
export ADMIN_KEY=${APISIX_ADMIN_KEY:edd1c9f034335f136f87ad84b625c8f1}
export GEMINI_API_KEY=AIzaSyCPgvfeFYEDRi4SASWFjPyqw2CfoKNVUH8

curl -sS "$ADMIN_API/apisix/admin/routes/gemini-chat" -X PUT \
  -H "X-API-KEY: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "uri": "/llm",
    "methods": ["POST"],
    "plugins": {
      "ai-proxy": {
        "provider": "openai-compatible",
        "auth": { "header": { "Authorization": "Bearer '"$GEMINI_API_KEY"'" } },
        "options": {
          "model": "gemini-1.5-pro"   // or gemini-1.5-flash, etc.
        },
        "override": {
          "endpoint": "https://generativelanguage.googleapis.com/v1beta/chat/completions"
        }
      }
    }
  }'
