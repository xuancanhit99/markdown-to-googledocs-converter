import io
import os
import markdown
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load biến môi trường từ file .env
load_dotenv()

# Load BASE_URL từ .env
BASE_URL = os.getenv("BASE_URL")
if not BASE_URL:
    raise Exception("BASE_URL chưa được cấu hình trong .env")

app = FastAPI()


class CreateDocRequest(BaseModel):
    output: str  # Nội dung Markdown
    fileName: str  # Tên file Google Docs cần tạo


@app.post("/create_google_doc")
async def create_google_doc(data: CreateDocRequest, request: Request):
    # Lấy header Authorization từ request
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Thiếu Authorization header")

    try:
        # Lấy access token từ header
        access_token = auth_header.split()[1]

        # Tạo credentials với các thông tin cần thiết cho refresh token
        creds = Credentials(
            token=access_token,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=[
                'https://www.googleapis.com/auth/documents',
                'https://www.googleapis.com/auth/drive.file'
            ]
        )

        # Khởi tạo services
        docs_service = build('docs', 'v1', credentials=creds, cache_discovery=False)

        # Tạo Google Doc trống
        doc = docs_service.documents().create(
            body={"title": data.fileName}
        ).execute()
        document_id = doc.get('documentId')

        # Chuẩn bị nội dung để update
        requests = [{
            'insertText': {
                'location': {
                    'index': 1
                },
                'text': data.output
            }
        }]

        # Update nội dung document
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()

        # Tạo URL của document
        doc_url = f"https://docs.google.com/document/d/{document_id}/edit"

        return {
            "document_id": document_id,
            "doc_url": doc_url,
            "base_url": BASE_URL
        }

    except HttpError as e:
        error_message = f"Google API error: {str(e)}"
        raise HTTPException(status_code=e.resp.status, detail=error_message)
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
