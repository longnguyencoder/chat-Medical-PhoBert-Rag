"""
Speech-to-Text Service (OpenAI Whisper API)
===========================================

Thay thế Whisper local bằng OpenAI Whisper API.
Chạy tốt trên Python 3.12, không cần cài torch hoặc whisper local.

Tính năng:
- Hỗ trợ mp3, wav, m4a, webm, ogg, flac
- Xử lý file tạm, validation
- Gọi Whisper API: gpt-4o-transcribe
"""

import os
import logging
import tempfile
from typing import Optional, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from openai import OpenAI
client = OpenAI()

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'webm', 'ogg', 'flac', 'mp4'}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


class SpeechService:
    def __init__(self):
        logger.info("SpeechService initialized using OpenAI Whisper API")

    def _load_model(self):
        """Không dùng Whisper local nữa"""
        return  # Giữ lại để không lỗi khi gọi

    def validate_audio_file(self, file: FileStorage) -> Tuple[bool, Optional[str]]:
        if not file:
            return False, "No file provided"

        if file.filename == '':
            return False, "No file selected"

        filename = file.filename.lower()
        ext = filename.rsplit('.', 1)[-1] if '.' in filename else ''

        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Unsupported format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)

        if size == 0:
            return False, "File is empty"

        if size > MAX_FILE_SIZE:
            return False, f"File too large ({size/1024/1024:.2f}MB). Max 25MB"

        logger.info(f"File validation ok: {filename} ({size/1024:.2f}KB)")
        return True, None

    def save_temp_file(self, file: FileStorage) -> str:
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[-1]

        temp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{ext}",
            prefix="audio_"
        )
        temp_path = temp.name
        file.save(temp_path)
        temp.close()

        logger.info(f"Temp audio saved: {temp_path}")
        return temp_path

    def transcribe_audio(self, audio_path: str, language: str = "vi") -> dict:
        try:
            logger.info(f"Calling Whisper API for file: {audio_path}")

            # Prompt giúp model hiểu context y tế tiếng Việt tốt hơn
            prompt = "Đây là câu hỏi về y tế, sức khỏe bằng tiếng Việt. Hãy phiên âm chính xác các thuật ngữ y khoa."

            with open(audio_path, "rb") as f:
                result = client.audio.transcriptions.create(
                    model="gpt-4o-transcribe",
                    file=f,
                    language=language,
                    prompt=prompt,  # Thêm context để cải thiện độ chính xác
                    temperature=0.0  # Giảm randomness, tăng consistency
                )

            text = result.text.strip()

            logger.info(f"Transcription OK. Text length: {len(text)} chars")

            return {
                "text": text,
                "language": language,
                "segments": [],
                "duration": 0
            }

        except Exception as e:
            logger.error(f"OpenAI transcription failed: {e}")
            raise RuntimeError(f"Failed to transcribe audio: {e}")

    def cleanup_temp_file(self, file_path: str):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temp file deleted: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete temp file {file_path}: {e}")

    def process_audio_file(self, file: FileStorage, language: str = "vi") -> dict:
        is_valid, err = self.validate_audio_file(file)
        if not is_valid:
            raise ValueError(err)

        temp_path = None
        try:
            temp_path = self.save_temp_file(file)
            result = self.transcribe_audio(temp_path, language)
            return result

        finally:
            if temp_path:
                self.cleanup_temp_file(temp_path)


speech_service = SpeechService()
