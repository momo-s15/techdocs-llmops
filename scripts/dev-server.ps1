param(
    [int]$Port = 8010
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Missing venv python at $python - run: python -m venv .venv"
}
Write-Host ('Starting TechDocs-LLMOps at http://127.0.0.1:{0}/docs (press Ctrl+C to stop)' -f $Port)
& $python -m uvicorn techdocs_llmops.api.main:app --reload --host 127.0.0.1 --port $Port
