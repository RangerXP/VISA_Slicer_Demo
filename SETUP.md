# VISA Slicer Demo - Setup Guide

## Quick Start (AAD Token - 5 min, fastest)

If you just want to **test the demo immediately**, use an AAD token:

1. Open https://app.powerbi.com in your browser
2. Press **F12** → **Network** tab
3. Click any report visual
4. Find a request to `wabi-west-us3-` → **Headers** → find `authorization: Bearer eyJ...`
5. Copy the token (everything after `Bearer `, just the long string)
6. Open `pbi-app-injection-demo.html` in your browser
7. Paste token into form
8. Select **AAD Token** type
9. Click **Embed Report**

⏰ **Caveat:** AAD tokens expire in ~1 hour.

---

## Preferred Local Run (service principal + in-app token refresh)

If the app is supposed to own embed token refresh, run the local demo server instead of generating and pasting a one-off token manually.

### Step 1: Install the Python dependency

```powershell
cd "c:\Users\seankelley\OneDrive - Microsoft\Documents\VISA\Slicer\Demo"
python -m pip install requests
```

### Step 2: Put credentials in `.env.local`

The repo already has the tenant, workspace, report, and client ID in `config.json`.
Keep the real secret in `.env.local` so the app can start without retyping shell variables each session.

```powershell
Copy-Item .\.env.local.example .\.env.local
```

Then edit `.env.local` and replace `YOUR_SECRET_VALUE_HERE` with the real client secret value.

`src\embed_token.py` and `src\demo_server.py` load `.env.local` automatically.

### Step 3: Start the local app server

```powershell
python .\src\demo_server.py
```

Then open:

```text
http://127.0.0.1:8000/pbi-app-injection-demo.html
```

What this gives you:
- The HTML page fetches its embed token from `/api/embed-token`
- The server reuses cached tokens when valid and refreshes them when needed
- The page renews the embedded report token before expiry by calling the same API again
- You no longer need to paste tokens into the form for the normal embed-token flow

If `/api/embed-token` returns an auth error, the client secret is wrong, expired, or belongs to a different app registration than the `clientId` in `config.json`.

---

## Proper Setup (Service Principal + Embed Token - 15 min, production-ready)

For a **persistent embed token** (needed for production or demos >1 hour):

### Fast Path: Provision with Script (recommended)

This repo now includes a provisioning script that creates:
- Azure AD app registration
- Service principal
- Client secret
- Power BI API app permissions (`Report.Read.All`, `Dataset.Read.All`)
- Optional admin consent
- `.env.local` with local credentials
- `config.json` auth metadata updates without persisting the secret

Run:

```powershell
# First-time only: install Azure CLI
winget install -e --id Microsoft.AzureCLI

# Then provision app registration + service principal and write .env.local
./scripts/provision_service_principal.ps1
```

Optional:

```powershell
# If you want to grant admin consent separately later
./scripts/provision_service_principal.ps1 -SkipAdminConsent
```

Then continue at **Step 5** below to add the service principal to your Power BI workspace.

---

### Step 1: Create Azure AD App Registration

1. Go to **Azure Portal** → **App registrations** → **New registration**
2. Name: `VISA Slicer Demo`
3. Redirect URI: `http://localhost` (or leave blank)
4. Click **Register**
5. Copy the **Application (client) ID** from the Overview page

### Step 2: Create Client Secret

1. Go to **Certificates & secrets** → **New client secret**
2. Description: `VISA Demo Embed`
3. Expires: `12 months` (adjust as needed)
4. Click **Add**
5. ⚠️ **Copy the VALUE immediately** (not the ID) — you won't see it again

### Step 3: Grant API Permissions

1. Go to **API permissions** → **Add a permission**
2. Select **Power BI Service**
3. Choose **Application permissions** (not Delegated)
4. Check: `Report.Read.All`, `Dataset.Read.All`
5. Click **Add permissions**
6. Click **Grant admin consent for [Organization]** (needs admin)

### Step 4: Update local credentials

Preferred local-dev path: create `.env.local` with your real credentials:

```powershell
Copy-Item .\.env.local.example .\.env.local
```

Then set:

```text
PBI_CLIENT_ID=YOUR-CLIENT-ID-FROM-STEP-1
PBI_CLIENT_SECRET=YOUR-SECRET-VALUE-FROM-STEP-2
PBI_TENANT_ID=YOUR-TENANT-ID
PBI_SCOPE=00000009-0000-0000-c000-000000000000/.default
```

`config.json` should keep the secret placeholder so credentials do not get committed into the repo.

Example `config.json` auth block:

```json
{
  "fabric": { ... },
  "auth": {
    "clientId": "YOUR-CLIENT-ID-FROM-STEP-1",
    "clientSecret": "LOAD_FROM_ENV_VAR_PBI_CLIENT_SECRET",
    "tenantId": "YOUR-TENANT-ID",
    "scope": "00000009-0000-0000-c000-000000000000/.default"
  },
  ...
}
```

### Step 5: Add Service Principal to Power BI Workspace

1. Go to **Power BI Admin Portal** → **Tenant settings** → find **Service principals**
2. Toggle **Allow service principals to use Power BI APIs** → ON
3. In your **VISA workspace** → **Workspace settings** → **Members**
4. Add member: paste the **Client ID** from Step 1
5. Select role: **Admin**

### Step 6: Generate Embed Token

```bash
cd "path/to/Demo/src"
python embed_token.py
```

Note: `embed_token.py` is still useful for diagnostics, but the preferred way to run the actual demo is `python .\src\demo_server.py` so the application can request and refresh tokens itself.

This will:
- ✅ Load your credentials from `.env.local` or environment variables
- ✅ Authenticate with Azure AD
- ✅ Generate a 60-minute embed token
- ✅ Print it to console
- ✅ Save it to `../.embed-token`

### Step 7: Use the Token

1. Copy the token from the console output
2. Open `pbi-app-injection-demo.html`
3. Paste token into the form
4. Select **Embed Token** type
5. Click **Embed Report**

✅ Demo is now live with all filters working!

---

## Troubleshooting

**"Missing configuration" error:**
- Verify `.env.local` exists and has the real Client ID, Secret, and Tenant ID
- Or provide `PBI_CLIENT_ID`, `PBI_CLIENT_SECRET`, `PBI_TENANT_ID`, and `PBI_SCOPE` in the shell

**"401 Unauthorized" from token generator:**
- Verify the Client ID and Secret in `.env.local` are correct
- Check that API permissions were granted (Step 3)
- Check that admin consent was granted

**"404 Not Found" in HTML embed:**
- Verify token is correct and not expired
- Verify Report ID and Workspace ID in the HTML form match config.json
- Check browser F12 → Console for detailed error

**Report doesn't respond to filters:**
- Check browser Console for errors
- Verify table/column names match your report's semantic model
- Ensure token has `Report.Read.All` permission

---

## Next Steps

Once the demo is working:

1. **Populate real filter values** from your VISA report:
   - Open report in Power BI Desktop
   - Drop each slicer column on a table visual
   - Copy distinct values
   - Paste into the `catalog[]` object in the HTML

2. **Test cascade logic**: Segment → Product

3. **Demo the four pain points**:
   - ✓ No Ctrl+Click (mobile-friendly)
   - ✓ Deferred execution (Apply button required)
   - ✓ Cascading (Product list updates when Segment changes)
   - ✓ Single updateFilters() call (one API roundtrip)

4. **Share with VISA team** — link to the HTML file + this guide
