# Script Tự Động Tải và Cài Đặt ffmpeg
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INSTALLING FFMPEG FOR SPEECH-TO-TEXT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kiểm tra ffmpeg đã cài chưa
Write-Host "[1/5] Checking if ffmpeg is already installed..." -ForegroundColor Yellow
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "  ✓ ffmpeg is already installed: $ffmpegVersion" -ForegroundColor Green
    Write-Host ""
    Write-Host "ffmpeg is ready! You can now use Speech-to-Text API." -ForegroundColor Green
    exit 0
} catch {
    Write-Host "  ✗ ffmpeg not found. Installing..." -ForegroundColor Yellow
}

# Tạo thư mục ffmpeg
Write-Host ""
Write-Host "[2/5] Creating ffmpeg directory..." -ForegroundColor Yellow
$ffmpegDir = "C:\ffmpeg"
if (-not (Test-Path $ffmpegDir)) {
    New-Item -ItemType Directory -Path $ffmpegDir | Out-Null
    Write-Host "  ✓ Created directory: $ffmpegDir" -ForegroundColor Green
} else {
    Write-Host "  ✓ Directory already exists: $ffmpegDir" -ForegroundColor Green
}

# Tải ffmpeg
Write-Host ""
Write-Host "[3/5] Downloading ffmpeg..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes (~100MB)..." -ForegroundColor Gray

$ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$zipPath = "$env:TEMP\ffmpeg.zip"

try {
    # Tải file
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $zipPath -UseBasicParsing
    Write-Host "  ✓ Downloaded ffmpeg" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to download ffmpeg: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download manually from:" -ForegroundColor Yellow
    Write-Host "  https://www.gyan.dev/ffmpeg/builds/" -ForegroundColor Cyan
    exit 1
}

# Giải nén
Write-Host ""
Write-Host "[4/5] Extracting ffmpeg..." -ForegroundColor Yellow
try {
    Expand-Archive -Path $zipPath -DestinationPath $env:TEMP -Force
    
    # Tìm thư mục ffmpeg đã giải nén
    $extractedDir = Get-ChildItem -Path $env:TEMP -Directory | Where-Object { $_.Name -like "ffmpeg-*" } | Select-Object -First 1
    
    if ($extractedDir) {
        # Copy bin folder vào C:\ffmpeg
        Copy-Item -Path "$($extractedDir.FullName)\bin\*" -Destination "$ffmpegDir\bin\" -Recurse -Force
        Write-Host "  ✓ Extracted to $ffmpegDir\bin" -ForegroundColor Green
        
        # Cleanup
        Remove-Item -Path $zipPath -Force
        Remove-Item -Path $extractedDir.FullName -Recurse -Force
    } else {
        throw "Could not find extracted ffmpeg directory"
    }
} catch {
    Write-Host "  ✗ Failed to extract: $_" -ForegroundColor Red
    exit 1
}

# Thêm vào PATH
Write-Host ""
Write-Host "[5/5] Adding ffmpeg to PATH..." -ForegroundColor Yellow

$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$ffmpegBinPath = "$ffmpegDir\bin"

if ($currentPath -notlike "*$ffmpegBinPath*") {
    try {
        # Cần quyền Administrator
        $newPath = $currentPath + ";" + $ffmpegBinPath
        [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
        Write-Host "  ✓ Added to PATH (requires restart)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Could not add to PATH automatically" -ForegroundColor Yellow
        Write-Host "  Please add manually: $ffmpegBinPath" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✓ Already in PATH" -ForegroundColor Green
}

# Tổng kết
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INSTALLATION COMPLETE!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ ffmpeg installed to: $ffmpegDir\bin" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Please restart your terminal/PowerShell" -ForegroundColor Yellow
Write-Host "Then verify with: ffmpeg -version" -ForegroundColor Yellow
Write-Host ""
Write-Host "After restart, Speech-to-Text API will work!" -ForegroundColor Green
Write-Host ""
