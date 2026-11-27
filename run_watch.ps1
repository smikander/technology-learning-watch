$ErrorActionPreference = "Stop"

$projectDir = $PSScriptRoot
$python = Join-Path $projectDir ".venv\Scripts\python.exe"
$mainScript = Join-Path $projectDir "main.py"
$logDir = Join-Path $projectDir "logs"
$model = "gemma-3-4b-it"
$apiUrl = "http://127.0.0.1:1234/v1/models"

New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = Join-Path $logDir "watch-$timestamp.log"

Start-Transcript -Path $logFile

try {
    Write-Host "Technology & Learning Watch"
    Write-Host "Started: $(Get-Date)"

    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        throw "Python virtual environment not found: $python"
    }

    if (-not (Test-Path -LiteralPath $mainScript -PathType Leaf)) {
        throw "Main script not found: $mainScript"
    }
    
    # Check the local API server
    try {
        $response = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 5
        Write-Host "LM Studio server is running."
    }
    catch {
        Write-Host "Starting LM Studio server..."

        lms server start --port 1234 --bind 127.0.0.1

        if ($LASTEXITCODE -ne 0) {
            throw "Server startup failed."
        }

        $serverReady = $false

        for ($attempt = 1; $attempt -le 10; $attempt++) {
            try {
                $response = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 3
                $serverReady = $true
                break
            }
            catch {
                Write-Host "Waiting for LM Studio server ($attempt/10)..."
                Start-Sleep -Seconds 2
            }
        }

        if (-not $serverReady) {
            throw "LM Studio server did not become available."
        }
    }

    # Check model availability
    $response = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 10
    $availableModels = @($response.data.id)

    if ($model -notin $availableModels) {
        Write-Host "Loading model: $model"

        lms load $model

        if ($LASTEXITCODE -ne 0) {
            throw "Model loading failed."
        }
    }
    else {
        Write-Host "Model is available."
    }

    # Run Python application
    Write-Host "Starting Python application..."

    Set-Location $projectDir
    $env:PYTHONUTF8 = "1"

    & $python -u $mainScript

    if ($LASTEXITCODE -ne 0) {
        throw "Python application failed."
    }

    Write-Host "Finished: $(Get-Date)"
}
catch {
    Write-Host "ERROR: $_"
    exit 1
}
finally {
    Stop-Transcript
}