import io
import os
import markdown
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Load biến môi trường từ file .env
load_dotenv()

# Load BASE_URL từ .env
BASE_URL = os.getenv("BASE_URL")
if not BASE_URL:
    raise Exception("BASE_URL chưa được cấu hình trong .env")

app = FastAPI()

# Model định nghĩa dữ liệu đầu vào
class CreateDocRequest(BaseModel):
    output: str      # Nội dung Markdown
    fileName: str    # Tên file Google Docs cần tạo

@app.post("/create_google_doc")
async def create_google_doc(data: CreateDocRequest, request: Request):
    # Lấy header Authorization từ request
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=400, detail="Thiếu Authorization header")

    token_parts = auth_header.split()
    if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
        raise HTTPException(status_code=400, detail="Định dạng Authorization header không hợp lệ")

    access_token = token_parts[1]

    # Tạo credentials từ access token
    creds = Credentials(token=access_token)
    # Lưu ý: Credentials này chỉ chứa access_token. Nếu token hết hạn, bạn cần có cơ chế refresh hoặc đảm bảo token luôn hợp lệ.

    # Khởi tạo Google Drive API service sử dụng credentials trên
    drive_service = build('drive', 'v3', credentials=creds)

    try:
        # Chuyển đổi Markdown sang HTML
        html_content = markdown.markdown(data.output)

        # Metadata cho file Google Docs mới
        file_metadata = {
            'name': data.fileName,
            'mimeType': 'application/vnd.google-apps.document'
        }

        # Chuyển nội dung HTML thành bytes và tạo đối tượng media upload
        html_bytes = html_content.encode('utf-8')
        media = MediaIoBaseUpload(io.BytesIO(html_bytes), mimetype='text/html')

        # Tạo file Google Docs thông qua Drive API (với khả năng convert HTML sang Docs)
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        document_id = file.get('id')
        doc_url = f"https://docs.google.com/document/d/{document_id}/edit"

        # Response có thể bao gồm BASE_URL để xác nhận cấu hình nếu cần
        return {"document_id": document_id, "doc_url": doc_url, "base_url": BASE_URL}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))