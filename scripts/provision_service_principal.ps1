param(
    [string]$AppDisplayName = "VISA Slicer Demo",
    [string]$SecretDisplayName = "VISA Demo Embed",
    [int]$SecretYears = 1,
    [switch]$SkipAdminConsent
)

$ErrorActionPreference = "Stop"

function Require-Cli {
    if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
        Write-Error "Azure CLI ('az') is not installed. Install it first, then rerun this script."
    }
}

function Ensure-Login {
    try {
        az account show --output none | Out-Null
    } catch {
        Write-Host "Azure login required. Launching 'az login'..."
        az login --output none
    }
}

function Get-PowerBiAppRoleId {
    param(
        [Parameter(Mandatory = $true)][object]$Roles,
        [Parameter(Mandatory = $true)][string]$RoleValue
    )

    $role = $Roles | Where-Object {
        $_.value -eq $RoleValue -and ($_.allowedMemberTypes -contains "Application")
    } | Select-Object -First 1

    if (-not $role) {
        Write-Host "Note: Power BI app role '$RoleValue' not found. This is expected for service principal (app-owns-data)." -ForegroundColor Yellow
        return $null
    }

    return $role.id
}

function Update-Config {
    param(
        [Parameter(Mandatory = $true)][string]$ConfigPath,
        [Parameter(Mandatory = $true)][string]$ClientId,
        [Parameter(Mandatory = $true)][string]$ClientSecret,
        [Parameter(Mandatory = $true)][string]$TenantId
    )

    $config = Get-Content -Raw -Path $ConfigPath | ConvertFrom-Json

    if (-not $config.auth) {
        $config | Add-Member -MemberType NoteProperty -Name auth -Value (@{})
    }

    $config.auth.clientId = $ClientId
    $config.auth.clientSecret = $ClientSecret
    $config.auth.tenantId = $TenantId

    if (-not $config.auth.scope) {
        $config.auth.scope = "https://analysis.windows.net/.default"
    }

    $config | ConvertTo-Json -Depth 10 | Set-Content -Path $ConfigPath -Encoding UTF8
}

Require-Cli
Ensure-Login

$repoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $repoRoot "config.json"

if (-not (Test-Path $configPath)) {
    throw "config.json not found at $configPath"
}

$tenantId = az account show --query tenantId -o tsv
if (-not $tenantId) {
    throw "Unable to resolve tenant ID from current Azure login context."
}

Write-Host "Creating app registration: $AppDisplayName"
$appJson = az ad app create --display-name "$AppDisplayName" --sign-in-audience AzureADMyOrg --web-redirect-uris "http://localhost" --output json
$app = $appJson | ConvertFrom-Json

if (-not $app.appId) {
    throw "Failed to create app registration."
}

Write-Host "Creating service principal for appId: $($app.appId)"
az ad sp create --id $app.appId --output none

Write-Host "Creating client secret"
$clientSecret = az ad app credential reset --id $app.appId --display-name "$SecretDisplayName" --years $SecretYears --query password -o tsv
if (-not $clientSecret) {
    throw "Failed to create client secret."
}

# Power BI Service application ID (first-party API)
$pbiApiAppId = "00000009-0000-0000-c000-000000000000"

Write-Host "Resolving Power BI API app roles"
$pbiSpJson = az ad sp list --filter "appId eq '$pbiApiAppId'" --query "[0]" --output json
$pbiSp = $pbiSpJson | ConvertFrom-Json

if (-not $pbiSp -or -not $pbiSp.appRoles) {
    throw "Unable to resolve Power BI Service principal roles."
}

$datasetReadRoleId = Get-PowerBiAppRoleId -Roles $pbiSp.appRoles -RoleValue "Dataset.Read.All"
$reportReadRoleId = Get-PowerBiAppRoleId -Roles $pbiSp.appRoles -RoleValue "Report.Read.All"

if ($datasetReadRoleId -and $reportReadRoleId) {
    Write-Host "Adding API permissions: Dataset.Read.All, Report.Read.All"
    az ad app permission add --id $app.appId --api $pbiApiAppId --api-permissions "$datasetReadRoleId=Role" "$reportReadRoleId=Role" --output none

    if (-not $SkipAdminConsent) {
        Write-Host "Granting admin consent"
        az ad app permission admin-consent --id $app.appId --output none
    }
} else {
    Write-Host "Skipping Azure AD API permission grant (not applicable for service principal app-owns-data scenario)." -ForegroundColor Yellow
    Write-Host "Power BI permissions will be granted at the workspace level instead." -ForegroundColor Yellow
}

Write-Host "Updating config.json auth block"
Update-Config -ConfigPath $configPath -ClientId $app.appId -ClientSecret $clientSecret -TenantId $tenantId

Write-Host ""
Write-Host "Provisioning complete."
Write-Host "Client ID: $($app.appId)"
Write-Host "Tenant ID: $tenantId"
Write-Host "config.json updated with auth.clientId/auth.clientSecret/auth.tenantId"
Write-Host ""
Write-Host "NEXT STEPS (Power BI workspace configuration - required):"
Write-Host "1. Sign in to Power BI Admin Portal (admin.powerbi.com)"
Write-Host "2. Tenant settings -> enable 'Service principals can use Power BI APIs' (or 'Service principals' section)"
Write-Host "3. Go to VISA workspace -> Members"
Write-Host "4. Add member: $($app.appId)"
Write-Host "5. Select role: Admin"
Write-Host "6. Then run: python src/embed_token.py"
