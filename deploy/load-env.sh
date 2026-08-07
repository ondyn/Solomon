#!/usr/bin/env sh

# Load only deployment settings from a Docker-style dotenv file.
# Existing exported values take precedence over values in the file.
SOLOMON_ENV_FILE="${SOLOMON_ENV_FILE:-.env}"

if [ -f "$SOLOMON_ENV_FILE" ]; then
  for env_name in PROJECT_ID REGION ZONE VM_NAME DNS_ZONE DOMAIN ACME_EMAIL NETBOX_VERSION; do
    if [ -n "$(printenv "$env_name" 2>/dev/null || true)" ]; then
      continue
    fi

    env_value="$(awk -v name="$env_name" '
      index($0, name "=") == 1 {
        sub(/^[^=]*=/, "")
        sub(/\r$/, "")
        print
        exit
      }
    ' "$SOLOMON_ENV_FILE")"

    if [ -n "$env_value" ]; then
      case "$env_value" in
        \"*\") env_value="${env_value#\"}"; env_value="${env_value%\"}" ;;
        \'*\') env_value="${env_value#\'}"; env_value="${env_value%\'}" ;;
      esac
      export "$env_name=$env_value"
    fi
  done
fi

unset env_name env_value