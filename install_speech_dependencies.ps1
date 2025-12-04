# Script Tự Động Cài Đặt Dependencies cho Speech-to-Text API
# ==============================================================
# Script này sẽ cài đặt tất cả dependencies cần thiết

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SPEECH-TO-TEXT API - AUTO INSTALL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kiểm tra Python
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found!" -ForegroundColor Red
    Write-Host "  Please install Python 3.8+ from python.org" -ForegroundColor Red
    exit 1
}

# Kiểm tra pip
Write-Host ""
Write-Host "[2/5] Checking pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>&1
    Write-Host "  ✓ $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ pip not found!" -ForegroundColor Red
    exit 1
}

# Cài đặt Flask và dependencies cơ bản
Write-Host ""
Write-Host "[3/5] Installing Flask and basic dependencies..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray

$packages = @(
    "Flask==3.0.1",
    "flask-restx",
    "flask-cors",
    "flask-mail",
    "python-dotenv",
    "PyJWT",
    "bcrypt",
    "Werkzeug==3.0.1"
)

foreach ($package in $packages) {
    Write-Host "  Installing $package..." -ForegroundColor Gray
    pip install $package --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✓ $package installed" -ForegroundColor Green
    } else {
        Write-Host "    ✗ Failed to install $package" -ForegroundColor Red
    }
}

# Cài đặt Speech-to-Text dependencies
Write-Host ""
Write-Host "[4/5] Installing Speech-to-Text dependencies..." -ForegroundColor Yellow
Write-Host "  ⚠ This will download ~150MB for Whisper model" -ForegroundColor Yellow

$speechPackages = @(
    "openai-whisper",
    "ffmpeg-python"
)

foreach ($package in $speechPackages) {
    Write-Host "  Installing $package..." -ForegroundColor Gray
    pip install $package --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✓ $package installed" -ForegroundColor Green
    } else {
        Write-Host "    ✗ Failed to install $package" -ForegroundColor Red
    }
}

# Kiểm tra ffmpeg
Write-Host ""
Write-Host "[5/5] Checking ffmpeg..." -ForegroundColor Yellow
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "  ✓ $ffmpegVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ ffmpeg not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  To install ffmpeg:" -ForegroundColor Yellow
    Write-Host "    Option 1: choco install ffmpeg" -ForegroundColor Gray
    Write-Host "    Option 2: Download from https://ffmpeg.org/download.html" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  ⚠ Speech-to-Text will NOT work without ffmpeg!" -ForegroundColor Yellow
}

# Tổng kết
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INSTALLATION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Test imports
Write-Host ""
Write-Host "Testing installations..." -ForegroundColor Yellow

$testScript = @"
try:
    import flask
    print('✓ Flask:', flask.__version__)
except:
    print('✗ Flask: NOT INSTALLED')

try:
    import whisper
    print('✓ Whisper:', whisper.__version__)
except:
    print('✗ Whisper: NOT INSTALLED')

try:
    import jwt
    print('✓ PyJWT: OK')
except:
    print('✗ PyJWT: NOT INSTALLED')
"@

python -c $testScript

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Make sure ffmpeg is installed (see above)" -ForegroundColor White
Write-Host "2. Run server: python main.py" -ForegroundColor White
Write-Host "3. Open browser: http://localhost:5000/docs" -ForegroundColor White
Write-Host "4. Test Speech API in Swagger UI" -ForegroundColor White
Write-Host ""
Write-Host "✓ Installation complete!" -ForegroundColor Green
Write-Host ""
