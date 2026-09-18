[CmdletBinding()]
param(
    [ValidateSet("fixed", "vulnerable")]
    [string]$Profile = "fixed",
    [switch]$SkipVulnerableScan
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repositoryRoot

function Invoke-RequiredCommand {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command $($Arguments -join ' ')"
    }
}

Write-Host "[1/3] Scanning fixed application with Semgrep..."
Invoke-RequiredCommand "semgrep" @(
    "scan",
    "--config", "p/owasp-top-ten",
    "--error",
    "--exclude-rule", "python.flask.security.audit.app-run-param-config.avoid_app_run_with_bad_host",
    "--json-output", "semgrep-fixed.json",
    "--sarif-output", "semgrep-fixed.sarif",
    "web_app_fixed"
)

if (-not $SkipVulnerableScan) {
    Write-Host "[2/3] Scanning vulnerable application and exporting findings..."
    semgrep scan --config p/owasp-top-ten `
        --json-output semgrep-vulnerable.json `
        --sarif-output semgrep-vulnerable.sarif `
        web_app
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "The vulnerable training app contains expected findings; continuing to deployment."
    }
}
else {
    Write-Host "[2/3] Skipping vulnerable-app scan."
}

Write-Host "[3/3] Building images and deploying '$Profile' profile..."
Invoke-RequiredCommand "docker" @("compose", "--profile", "vulnerable", "--profile", "fixed", "build")
Invoke-RequiredCommand "docker" @("compose", "--profile", $Profile, "up", "-d")

Write-Host "Deployment complete: http://localhost:5656/"