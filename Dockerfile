FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

EXPOSE 5000

# CMD ["waitress-serve", "--listen=*:5000", "app:app"]
CMD ["python", "prod-server.py"]

