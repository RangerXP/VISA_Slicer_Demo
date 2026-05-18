#!/usr/bin/env python3
"""Power BI embed token generator with persistent local token cache.

This script implements service-principal auth (client credentials flow) and
persists both AAD and embed token metadata in a local cache file. It reuses
valid cached tokens and refreshes only when close to expiration.

Usage:
    python src/embed_token.py
    python src/embed_token.py --refresh
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
ENV_LOCAL_PATH = ROOT / ".env.local"
EMBED_TOKEN_FILE = ROOT / ".embed-token"
TOKEN_CACHE_FILE = ROOT / ".token-cache.json"


def _utc_now():
    return datetime.now(timezone.utc)


def _parse_iso_utc(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _to_iso_utc(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _decode_jwt_payload(token):
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload_b64 = parts[1]
        padding = "=" * (-len(payload_b64) % 4)
        decoded = base64.urlsafe_b64decode(payload_b64 + padding)
        return json.loads(decoded.decode("utf-8"))
    except Exception:
        return {}


def _token_expiry_from_jwt(token):
    payload = _decode_jwt_payload(token)
    exp = payload.get("exp")
    if not exp:
        return None
    return datetime.fromtimestamp(exp, tz=timezone.utc)


def _load_cache():
    if not TOKEN_CACHE_FILE.exists():
        return {}
    try:
        return json.loads(TOKEN_CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_cache(cache):
    TOKEN_CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _strip_optional_quotes(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _load_env_file(env_path):
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export "):].strip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_optional_quotes(value.strip())

        if key and key not in os.environ:
            os.environ[key] = value

def load_config():
    """Load configuration from config.json"""
    if not CONFIG_PATH.exists():
        print(f"Error: config.json not found at {CONFIG_PATH}")
        sys.exit(1)

    _load_env_file(ENV_LOCAL_PATH)

    with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
        config = json.load(f)

    auth = config.setdefault("auth", {})
    fabric = config.setdefault("fabric", {})

    env_client_id = os.getenv("PBI_CLIENT_ID")
    env_client_secret = os.getenv("PBI_CLIENT_SECRET")
    env_tenant_id = os.getenv("PBI_TENANT_ID")
    env_scope = os.getenv("PBI_SCOPE")

    if env_client_id:
        auth["clientId"] = env_client_id
    if env_client_secret:
        auth["clientSecret"] = env_client_secret
    if env_scope:
        auth["scope"] = env_scope

    # Support both auth.tenantId and fabric.tenantId from existing docs/config.
    if env_tenant_id:
        auth["tenantId"] = env_tenant_id
    elif not auth.get("tenantId") and fabric.get("tenantId"):
        auth["tenantId"] = fabric.get("tenantId")

    auth.setdefault("scope", "https://analysis.windows.net/.default")

    # Validate required fields
    required_fields = ["clientId", "clientSecret", "tenantId"]
    missing = []

    for field in required_fields:
        value = auth.get(field)
        if not value or str(value).startswith("TODO"):
            missing.append(f"auth.{field}")

    for field in ["workspaceId", "reportId"]:
        value = fabric.get(field)
        if not value or str(value).startswith("TODO"):
            missing.append(f"fabric.{field}")

    if missing:
        print("Missing configuration:")
        for field in missing:
            print(f"   - {field}")
        print("\nSet these in config.json, .env.local, or env vars:")
        print("   PBI_CLIENT_ID, PBI_CLIENT_SECRET, PBI_TENANT_ID, PBI_SCOPE")
        sys.exit(1)

    return config

def get_aad_token(config, force_refresh=False):
    """Get AAD token using service principal credentials with local caching."""
    cache = _load_cache()
    cached = cache.get("aad")

    if not force_refresh and cached:
        expires_at = _parse_iso_utc(cached.get("expiresAt"))
        if expires_at and expires_at > (_utc_now() + timedelta(minutes=5)):
            return cached.get("token")

    tenant_id = config["auth"]["tenantId"]
    client_id = config["auth"]["clientId"]
    client_secret = config["auth"]["clientSecret"]

    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": config["auth"].get("scope", "https://analysis.windows.net/.default"),
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        payload_json = response.json()
        token = payload_json["access_token"]
        expires_in = int(payload_json.get("expires_in", 3599))

        cache["aad"] = {
            "token": token,
            "expiresAt": _to_iso_utc(_utc_now() + timedelta(seconds=expires_in)),
        }
        _save_cache(cache)
        return token
    except requests.exceptions.RequestException as e:
        print(f"Failed to get AAD token: {e}")
        if hasattr(e, "response") and e.response is not None and hasattr(e.response, "text"):
            print(f"   Response: {e.response.text}")
        sys.exit(1)


def get_report_dataset_id(config, aad_token):
    """Resolve datasetId from report metadata when not explicitly configured."""
    explicit_dataset_id = config.get("fabric", {}).get("datasetId")
    if explicit_dataset_id and not str(explicit_dataset_id).startswith("TODO"):
        return explicit_dataset_id

    workspace_id = config["fabric"]["workspaceId"]
    report_id = config["fabric"]["reportId"]
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
    headers = {"Authorization": f"Bearer {aad_token}"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get("datasetId")
    except requests.exceptions.RequestException as e:
        print(f"Failed to resolve dataset ID from report metadata: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Status: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def generate_embed_token(config, aad_token, force_refresh=False):
    """Generate Power BI embed token with cache reuse."""
    cache = _load_cache()
    cached = cache.get("embed")

    if not force_refresh and cached:
        expires_at = _parse_iso_utc(cached.get("expiresAt"))
        if expires_at and expires_at > (_utc_now() + timedelta(minutes=5)):
            return cached.get("token"), expires_at

    report_id = config["fabric"]["reportId"]
    workspace_id = config["fabric"]["workspaceId"]
    dataset_id = get_report_dataset_id(config, aad_token)

    url = "https://api.powerbi.com/v1.0/myorg/GenerateToken"

    headers = {
        "Authorization": f"Bearer {aad_token}",
        "Content-Type": "application/json",
    }

    expiration = _to_iso_utc(_utc_now() + timedelta(minutes=60))

    payload = {
        "reports": [
            {
                "id": report_id
            }
        ],
        "datasets": [
            {
                "id": dataset_id
            }
        ],
        "targetWorkspaces": [
            {
                "id": workspace_id
            }
        ],
        "accessLevel": "View",
        "expiration": expiration,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        payload_json = response.json()
        token = payload_json["token"]

        embed_expiry = (
            _parse_iso_utc(payload_json.get("expiration"))
            or _token_expiry_from_jwt(token)
            or (_utc_now() + timedelta(minutes=60))
        )

        cache["embed"] = {
            "token": token,
            "expiresAt": _to_iso_utc(embed_expiry),
            "workspaceId": workspace_id,
            "reportId": report_id,
            "datasetId": dataset_id,
        }
        _save_cache(cache)
        return token, embed_expiry
    except requests.exceptions.RequestException as e:
        print(f"Failed to generate embed token: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   Status: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Generate/reuse Power BI embed token")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force refresh both AAD and embed tokens, ignoring local cache.",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Power BI Embed Token Generator")
    print("=" * 70)

    # Load config
    print("\nLoading configuration...")
    config = load_config()
    print(f"   Workspace: {config['fabric'].get('workspaceName', 'N/A')}")
    print(f"   Report: {config['fabric'].get('reportName', 'N/A')}")

    print("\nAuthenticating with Azure AD...")
    aad_token = get_aad_token(config, force_refresh=args.refresh)
    print("   AAD token ready")

    print("\nGenerating Power BI embed token...")
    embed_token, embed_expiry = generate_embed_token(
        config,
        aad_token,
        force_refresh=args.refresh,
    )
    print("   Embed token ready")
    print(f"   Expires (UTC): {_to_iso_utc(embed_expiry)}")

    # Output token
    print("\n" + "=" * 70)
    print("EMBED TOKEN (copy and paste into HTML form)")
    print("=" * 70)
    print(embed_token)
    print("=" * 70)

    with open(EMBED_TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(embed_token)
    print(f"\nToken also saved to: {EMBED_TOKEN_FILE}")
    print(f"Cache metadata saved to: {TOKEN_CACHE_FILE}")

    return embed_token

if __name__ == "__main__":
    main()
