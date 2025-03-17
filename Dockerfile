# Sử dụng image Python chính thức
FROM python:3.11-slim

# Đặt working directory
WORKDIR /app

# Copy file requirements.txt và cài đặt các package
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Expose cổng 8000 để truy cập FastAPI
EXPOSE 1412

# Chạy ứng dụng với uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "1412"]
