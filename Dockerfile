FROM python:3.9-alpine

WORKDIR /backend_app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "toir_app.main:toir_app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
