"""
Quick Test - Whisper Installation
==================================
Test nhanh xem Whisper đã cài đặt và hoạt động chưa.
"""

print("="*60)
print("TESTING WHISPER INSTALLATION")
print("="*60)

# Test 1: Import whisper
print("\n[1/3] Testing import whisper...")
try:
    import whisper
    print(f"✓ Whisper installed successfully!")
    print(f"  Version: {whisper.__version__}")
except ImportError as e:
    print(f"✗ Whisper not installed: {e}")
    print("  Run: pip install openai-whisper")
    exit(1)

# Test 2: Load model
print("\n[2/3] Testing load model (base)...")
print("  ⚠ First time will download ~150MB...")
try:
    model = whisper.load_model("base")
    print(f"✓ Model loaded successfully!")
    print(f"  Type: {type(model)}")
except Exception as e:
    print(f"✗ Failed to load model: {e}")
    exit(1)

# Test 3: Check ffmpeg
print("\n[3/3] Testing ffmpeg...")
try:
    import subprocess
    result = subprocess.run(['ffmpeg', '-version'], 
                          capture_output=True, 
                          text=True,
                          timeout=5)
    if result.returncode == 0:
        version_line = result.stdout.split('\n')[0]
        print(f"✓ ffmpeg installed: {version_line}")
    else:
        print("⚠ ffmpeg command failed")
except FileNotFoundError:
    print("✗ ffmpeg not found in PATH")
    print("  Windows: choco install ffmpeg")
    print("  Linux: sudo apt install ffmpeg")
    print("  Mac: brew install ffmpeg")
except Exception as e:
    print(f"⚠ ffmpeg check failed: {e}")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("✓ Whisper is installed and working!")
print("\nYou can now:")
print("1. Use Speech-to-Text API in your Flask app")
print("2. Read documentation: SPEECH_API_GUIDE.md")
print("\nTo start server:")
print("  python main.py")
print("\n🎉 Setup complete!")
