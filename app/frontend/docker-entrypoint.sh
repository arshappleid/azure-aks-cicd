#!/bin/sh
# Generates /usr/share/nginx/html/env-config.js at container startup.
# Exposes runtime env vars to the React app via window._env_
# without requiring a rebuild — the same image works in any environment.
#
# Set API_URL in docker-compose.yaml:
#   environment:
#     - API_URL=http://your-backend:8000/info

set -e

ENV_JS=/usr/share/nginx/html/env-config.js

echo "Generating ${ENV_JS} ..."
cat > "${ENV_JS}" <<EOF
window._env_ = {
  API_URL: "${API_URL:-}"
};
EOF

echo "  API_URL = ${API_URL:-<not set>}"

exec nginx -g 'daemon off;'
