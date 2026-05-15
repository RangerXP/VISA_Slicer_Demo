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

## Proper Setup (Service Principal + Embed Token - 15 min, production-ready)

For a **persistent embed token** (needed for production or demos >1 hour):

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

### Step 4: Update config.json

In your `config.json`, replace the TODOs:

```json
{
  "fabric": { ... },
  "auth": {
    "clientId": "YOUR-CLIENT-ID-FROM-STEP-1",
    "clientSecret": "YOUR-SECRET-VALUE-FROM-STEP-2",
    "scope": "https://analysis.windows.net/.default"
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

This will:
- ✅ Load your credentials from config.json
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
- Update `config.json` with real Client ID and Secret from Azure AD

**"401 Unauthorized" from token generator:**
- Verify Client ID and Secret are correct
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
