#!/bin/bash
# Script Tự Động Cài Đặt Dependencies cho Speech-to-Text API (Linux/Mac)
# ========================================================================

echo "========================================"
echo "SPEECH-TO-TEXT API - AUTO INSTALL"
echo "========================================"
echo ""

# Màu sắc
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Kiểm tra Python
echo -e "${YELLOW}[1/5] Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "  ${GREEN}✓ $PYTHON_VERSION${NC}"
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo -e "  ${GREEN}✓ $PYTHON_VERSION${NC}"
    PYTHON_CMD=python
else
    echo -e "  ${RED}✗ Python not found!${NC}"
    echo -e "  ${RED}Please install Python 3.8+${NC}"
    exit 1
fi

# Kiểm tra pip
echo ""
echo -e "${YELLOW}[2/5] Checking pip...${NC}"
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version)
    echo -e "  ${GREEN}✓ $PIP_VERSION${NC}"
    PIP_CMD=pip3
elif command -v pip &> /dev/null; then
    PIP_VERSION=$(pip --version)
    echo -e "  ${GREEN}✓ $PIP_VERSION${NC}"
    PIP_CMD=pip
else
    echo -e "  ${RED}✗ pip not found!${NC}"
    exit 1
fi

# Cài đặt Flask và dependencies cơ bản
echo ""
echo -e "${YELLOW}[3/5] Installing Flask and basic dependencies...${NC}"
echo -e "  This may take a few minutes..."

PACKAGES=(
    "Flask==3.0.1"
    "flask-restx"
    "flask-cors"
    "flask-mail"
    "python-dotenv"
    "PyJWT"
    "bcrypt"
    "Werkzeug==3.0.1"
)

for package in "${PACKAGES[@]}"; do
    echo -e "  Installing $package..."
    $PIP_CMD install "$package" --quiet
    if [ $? -eq 0 ]; then
        echo -e "    ${GREEN}✓ $package installed${NC}"
    else
        echo -e "    ${RED}✗ Failed to install $package${NC}"
    fi
done

# Cài đặt Speech-to-Text dependencies
echo ""
echo -e "${YELLOW}[4/5] Installing Speech-to-Text dependencies...${NC}"
echo -e "  ${YELLOW}⚠ This will download ~150MB for Whisper model${NC}"

SPEECH_PACKAGES=(
    "openai-whisper"
    "ffmpeg-python"
)

for package in "${SPEECH_PACKAGES[@]}"; do
    echo -e "  Installing $package..."
    $PIP_CMD install "$package" --quiet
    if [ $? -eq 0 ]; then
        echo -e "    ${GREEN}✓ $package installed${NC}"
    else
        echo -e "    ${RED}✗ Failed to install $package${NC}"
    fi
done

# Kiểm tra ffmpeg
echo ""
echo -e "${YELLOW}[5/5] Checking ffmpeg...${NC}"
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n 1)
    echo -e "  ${GREEN}✓ $FFMPEG_VERSION${NC}"
else
    echo -e "  ${RED}✗ ffmpeg not found!${NC}"
    echo ""
    echo -e "  ${YELLOW}To install ffmpeg:${NC}"
    echo -e "    Ubuntu/Debian: sudo apt install ffmpeg"
    echo -e "    Mac: brew install ffmpeg"
    echo ""
    echo -e "  ${YELLOW}⚠ Speech-to-Text will NOT work without ffmpeg!${NC}"
fi

# Tổng kết
echo ""
echo "========================================"
echo "INSTALLATION SUMMARY"
echo "========================================"

# Test imports
echo ""
echo -e "${YELLOW}Testing installations...${NC}"

$PYTHON_CMD << EOF
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
EOF

echo ""
echo "========================================"
echo "NEXT STEPS"
echo "========================================"
echo ""
echo "1. Make sure ffmpeg is installed (see above)"
echo "2. Run server: python main.py"
echo "3. Open browser: http://localhost:5000/docs"
echo "4. Test Speech API in Swagger UI"
echo ""
echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""
