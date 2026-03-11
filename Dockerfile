FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py", "--papers-dir", "papers", "--output-dir", "results", "--grobid-url", "http://grobid:8070/api/processFulltextDocument"]

