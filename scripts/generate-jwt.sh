#!/bin/sh
# Generate a JWT token for service registration.
# The create_jwt_token utility auto-resolves signing key from config:
#   - RS256: reads JWT_PRIVATE_KEY_PATH + JWT_PUBLIC_KEY_PATH from environment
#   - HS256: reads JWT_SECRET_KEY from environment
# No flags needed — utility reads JWT_ALGORITHM from environment.
set -eu

EMAIL="${PLATFORM_ADMIN_EMAIL:-admin@apollosai.dev}"
EXPIRY="${TOKEN_EXPIRY:-10080}"

python3 -m mcpgateway.utils.create_jwt_token \
  --username "$EMAIL" \
  --exp "$EXPIRY" \
  --admin 2>/dev/null
