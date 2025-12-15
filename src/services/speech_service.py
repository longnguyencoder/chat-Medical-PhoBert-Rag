"""
Speech-to-Text Service (OpenAI Whisper API)
===========================================
Service layer xử lý việc chuyển đổi giọng nói thành văn bản.

Thay đổi quan trọng:
- Trước đây: Sử dụng thư viện `whisper` local (nặng, tốn RAM, cần GPU).
- Hiện tại: Sử dụng OpenAI Whisper API (nhanh, chính xác, không tốn tài nguyên server).

Tính năng:
1. Validate file audio (định dạng, kích thước).
2. Lưu file tạm thời để upload lên API.
3. Gọi OpenAI API để transcribe.
4. Dọn dẹp file tạm sau khi xử lý xong.
"""

import os
import logging
import tempfile
from typing import Optional, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from openai import OpenAI
client = OpenAI() # Tự động load API Key từ biến môi trường OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Các định dạng audio hỗ trợ
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'webm', 'ogg', 'flac', 'mp4'}
# Giới hạn kích thước file (25MB là giới hạn của Whisper API)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


class SpeechService:
    def __init__(self):
        logger.info("SpeechService initialized using OpenAI Whisper API")

    def _load_model(self):
        """
        [Legacy] Placeholder cho hàm load model local cũ.
        Hiện tại không dùng nữa vì gọi API.
        """
        return

    def validate_audio_file(self, file: FileStorage) -> Tuple[bool, Optional[str]]:
        """
        Kiểm tra tính hợp lệ của file audio.
        
        Checklist:
        1. Có file không?
        2. Tên file có rỗng không?
        3. Đuôi file có trong danh sách hỗ trợ không?
        4. File có rỗng (0 bytes) không?
        5. File có vượt quá 25MB không?
        """
        if not file:
            return False, "No file provided"

        if file.filename == '':
            return False, "No file selected"

        filename = file.filename.lower()
        ext = filename.rsplit('.', 1)[-1] if '.' in filename else ''

        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Unsupported format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

        # Kiểm tra kích thước file
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0) # Reset con trỏ về đầu file để đọc lại

        if size == 0:
            return False, "File is empty"

        if size > MAX_FILE_SIZE:
            return False, f"File too large ({size/1024/1024:.2f}MB). Max 25MB"

        logger.info(f"File validation ok: {filename} ({size/1024:.2f}KB)")
        return True, None

    def save_temp_file(self, file: FileStorage) -> str:
        """
        Lưu file upload vào thư mục tạm thời của hệ thống.
        Cần thiết vì OpenAI API yêu cầu đường dẫn file thực hoặc binary stream.
        Dùng named temporary file để tránh trùng tên.
        """
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[-1]

        # Tạo file tạm
        temp = tempfile.NamedTemporaryFile(
            delete=False, # Không xóa ngay khi đóng (để còn đọc lại)
            suffix=f".{ext}",
            prefix="audio_"
        )
        temp_path = temp.name
        file.save(temp_path)
        temp.close()

        logger.info(f"Temp audio saved: {temp_path}")
        return temp_path

    def transcribe_audio(self, audio_path: str, language: str = "vi") -> dict:
        """
        Core function: Gọi OpenAI Whisper API.
        """
        try:
            logger.info(f"Calling Whisper API for file: {audio_path}")

            # Prompt phụ trợ: Giúp model định hướng ngữ cảnh Y Tế Tiếng Việt
            # Whisper dùng prompt để hiểu các từ chuyên ngành tốt hơn.
            prompt = "Đây là câu hỏi về y tế, sức khỏe bằng tiếng Việt. Hãy phiên âm chính xác các thuật ngữ y khoa."

            with open(audio_path, "rb") as f:
                # Gọi API transcription
                result = client.audio.transcriptions.create(
                    model="whisper-1", # Model chuẩn của OpenAI cho audio
                    file=f,
                    language=language, # 'vi' cho tiếng Việt
                    prompt=prompt,
                    temperature=0.0    # 0.0 để kết quả nhất quán nhất
                )

            text = result.text.strip()

            logger.info(f"Transcription OK. Text length: {len(text)} chars")

            return {
                "text": text,
                "language": language,
                "segments": [], # API trả về simple text, không có segments chi tiết như local
                "duration": 0   # API response basic không trả về duration
            }

        except Exception as e:
            logger.error(f"OpenAI transcription failed: {e}")
            raise RuntimeError(f"Failed to transcribe audio: {e}")

    def cleanup_temp_file(self, file_path: str):
        """Xóa file tạm để giải phóng dung lượng đĩa."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temp file deleted: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete temp file {file_path}: {e}")

    def process_audio_file(self, file: FileStorage, language: str = "vi") -> dict:
        """
        Quy trình xử lý đầy đủ:
        1. Validate
        2. Save Temp
        3. Transcribe
        4. Cleanup
        """
        # 1. Validate
        is_valid, err = self.validate_audio_file(file)
        if not is_valid:
            raise ValueError(err)

        temp_path = None
        try:
            # 2. Save
            temp_path = self.save_temp_file(file)
            
            # 3. Transcribe
            result = self.transcribe_audio(temp_path, language)
            return result

        finally:
            # 4. Cleanup (Luôn chạy dù có lỗi hay không)
            if temp_path:
                self.cleanup_temp_file(temp_path)


# Singleton instance
speech_service = SpeechService()
