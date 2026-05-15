#!/usr/bin/env python3
"""
Power BI Embed Token Generator

Generates a short-lived embed token for Power BI report embedding.
Uses service principal (app owns data) authentication.

Usage:
    python embed_token.py

Prerequisites:
    1. Create Azure AD app registration:
       - Azure Portal → App registrations → New registration
       - Name: "VISA Slicer Demo"
       - Redirect URI: http://localhost (not needed for service principal)
    
    2. Create client secret:
       - Certificates & secrets → New client secret
       - Copy the VALUE (not ID)
    
    3. Update config.json with:
       - clientId (from app registration Overview page)
       - clientSecret (from the secret you just created)
       - tenantId (from app registration Overview page)
    
    4. Enable Power BI API permissions:
       - App registrations → API permissions
       - Add: Power BI Service (app permission)
       - Grant admin consent
    
    5. Assign Power BI admin role:
       - Power BI admin portal → Tenant settings
       - Service principals → Enable (tick the box)
       - Power BI workspace → Add service principal as Admin
         (Use the app's client ID when adding)
"""

import json
import sys
import requests
from pathlib import Path
from datetime import datetime, timedelta

def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent / "config.json"
    
    if not config_path.exists():
        print(f"❌ Error: config.json not found at {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Validate required fields
    required_fields = ['clientId', 'clientSecret', 'tenantId']
    missing = []
    
    for field in required_fields:
        value = config.get('auth', {}).get(field)
        if not value or value.startswith('TODO'):
            missing.append(f"auth.{field}")
    
    if missing:
        print("❌ Missing configuration:")
        for field in missing:
            print(f"   - {field}")
        print("\nUpdate config.json with your Azure AD app credentials.")
        print("See the docstring in this script for setup instructions.")
        sys.exit(1)
    
    return config

def get_aad_token(config):
    """Get AAD token using service principal credentials"""
    tenant_id = config['auth']['tenantId']
    client_id = config['auth']['clientId']
    client_secret = config['auth']['clientSecret']
    
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://analysis.windows.net/.default'
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        return response.json()['access_token']
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get AAD token: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def generate_embed_token(config, aad_token):
    """Generate Power BI embed token"""
    report_id = config['fabric']['reportId']
    workspace_id = config['fabric']['workspaceId']
    
    url = "https://api.powerbi.com/v1.0/myorg/GenerateToken"
    
    headers = {
        'Authorization': f'Bearer {aad_token}',
        'Content-Type': 'application/json'
    }
    
    # Token valid for 60 minutes
    expiration = (datetime.utcnow() + timedelta(minutes=60)).isoformat() + 'Z'
    
    payload = {
        'reports': [
            {
                'id': report_id
            }
        ],
        'datasets': [
            {
                'id': workspace_id  # Workspace acts as the semantic model container
            }
        ],
        'targetWorkspaces': [
            {
                'id': workspace_id
            }
        ],
        'accessLevel': 'View',
        'expiration': expiration
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()['token']
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to generate embed token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def main():
    print("=" * 70)
    print("Power BI Embed Token Generator")
    print("=" * 70)
    
    # Load config
    print("\n📋 Loading configuration...")
    config = load_config()
    print(f"   ✓ Workspace: {config['fabric']['workspaceName']}")
    print(f"   ✓ Report: {config['fabric']['reportName']}")
    
    # Get AAD token (service principal)
    print("\n🔐 Authenticating with Azure AD...")
    aad_token = get_aad_token(config)
    print("   ✓ AAD token obtained")
    
    # Generate embed token
    print("\n🎫 Generating Power BI embed token...")
    embed_token = generate_embed_token(config, aad_token)
    print("   ✓ Embed token generated")
    print("   ✓ Valid for: 60 minutes")
    
    # Output token
    print("\n" + "=" * 70)
    print("EMBED TOKEN (copy and paste into HTML form)")
    print("=" * 70)
    print(embed_token)
    print("=" * 70)
    
    # Also save to file
    token_file = Path(__file__).parent.parent / ".embed-token"
    with open(token_file, 'w') as f:
        f.write(embed_token)
    print(f"\n💾 Token also saved to: {token_file}")
    print("   (automatically loaded if you run the script again)")
    
    return embed_token

if __name__ == "__main__":
    main()
