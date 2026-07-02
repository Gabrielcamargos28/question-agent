# PowerShell script to run SonarQube Scanner via Docker

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "          Pluri Question Agent - SonarQube Scan          " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# Check if SonarQube container is running
$sonarContainer = docker ps --filter "name=sonarqube" --format "{{.Status}}"
if (-not $sonarContainer) {
    Write-Host "[!] SonarQube local server is not running." -ForegroundColor Yellow
    Write-Host "[*] Starting SonarQube server via docker-compose..." -ForegroundColor Yellow
    docker-compose up -d
    
    Write-Host "[*] Waiting for SonarQube server to start (it may take 1-2 minutes to be fully online)..." -ForegroundColor Yellow
    Write-Host "[*] Access http://localhost:9000 in your browser." -ForegroundColor Yellow
    Write-Host "[*] Login: admin / admin (change on first login)." -ForegroundColor Yellow
    Write-Host "[*] Create a project named 'pluri-question-agent' and generate a User Token." -ForegroundColor Yellow
    Read-Host "Press ENTER once you have logged in and created your token to proceed..."
}

# Prompt for the SonarQube Authentication Token
$token = Read-Host "Enter your SonarQube Project Token"
if (-not $token) {
    Write-Host "[Error] Token cannot be empty. Aborting scan." -ForegroundColor Red
    Exit
}

# Run the SonarQube scanner container
Write-Host "[*] Running SonarQube Scanner container..." -ForegroundColor Cyan
docker run --rm `
  -v "${PWD}:/usr/src" `
  sonarsource/sonar-scanner-cli `
  "-Dsonar.host.url=http://host.docker.internal:9000" `
  "-Dsonar.login=$token"

Write-Host "[+] Scan complete! Check results at http://localhost:9000" -ForegroundColor Green
