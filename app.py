import os
import io
import markdown
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Load các biến môi trường từ file .env
load_dotenv()

# Lấy thông tin cấu hình từ .env
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not GOOGLE_APPLICATION_CREDENTIALS:
    raise Exception("Chưa cấu hình GOOGLE_APPLICATION_CREDENTIALS trong .env")

# Định nghĩa các scope cần thiết cho Google Docs và Drive API
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

# Khởi tạo credentials từ file service account
credentials = service_account.Credentials.from_service_account_file(
    GOOGLE_APPLICATION_CREDENTIALS, scopes=SCOPES)

# Khởi tạo service cho Google Drive API
drive_service = build('drive', 'v3', credentials=credentials)

app = FastAPI()

# Định nghĩa model cho dữ liệu đầu vào
class CreateDocRequest(BaseModel):
    output: str  # Nội dung Markdown
    fileName: str  # Tên file muốn tạo

@app.post("/create_google_doc")
async def create_google_doc(request: CreateDocRequest):
    try:
        # Chuyển đổi Markdown sang HTML
        html_content = markdown.markdown(request.output)

        # Chuẩn bị metadata cho file Google Docs
        file_metadata = {
            'name': request.fileName,
            'mimeType': 'application/vnd.google-apps.document'
        }

        # Chuyển nội dung HTML thành bytes và tạo media upload
        html_bytes = html_content.encode('utf-8')
        media = MediaIoBaseUpload(io.BytesIO(html_bytes), mimetype='text/html')

        # Tạo file Google Docs thông qua Drive API với chức năng convert
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        document_id = file.get('id')
        doc_url = f"https://docs.google.com/document/d/{document_id}/edit"

        return {"document_id": document_id, "doc_url": doc_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
