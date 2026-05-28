$ErrorActionPreference = "Continue"

Write-Host "== ReguThink sanitized showcase scan =="

$patterns = @(
  "api_key",
  "apikey",
  "secret",
  "password",
  "token",
  "credential",
  "Neo4j",
  "bolt://",
  "sk-",
  "AKIA",
  "BEGIN PRIVATE KEY",
  "10.53.150.122",
  "192.168.39.186"
)

Write-Host "`n== Sensitive keyword scan =="
Get-ChildItem -Recurse -File -Force |
  Where-Object { $_.FullName -notmatch "\\.git\\" } |
  Select-String -Pattern ($patterns -join "|") -CaseSensitive:$false |
  Select-Object Path, LineNumber, Line

Write-Host "`n== Files larger than 10MB =="
Get-ChildItem -Recurse -File -Force |
  Where-Object { $_.FullName -notmatch "\\.git\\" -and $_.Length -gt 10MB } |
  Select-Object FullName, Length

Write-Host "`n== Forbidden directories/files =="
$forbiddenPattern = "\\node_modules\\|\\dist\\|\\.venv\\|\\runtime_storage\\|\\uploads\\|\\downloads\\|\\legal_data\\|\\vector_backends\\|\\chroma|\\neo4j|current_backend\.json|\\.env$"
Get-ChildItem -Recurse -Force |
  Where-Object { $_.FullName -notmatch "\\.git\\" -and $_.Name -ne ".env.example" -and $_.FullName -match $forbiddenPattern } |
  Select-Object FullName

Write-Host "`nScan complete. This script reports findings only and does not delete files."
