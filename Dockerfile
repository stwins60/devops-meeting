FROM python:3.11-slim AS base

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt --no-cache-dir

FROM python:3.11-slim AS dev

WORKDIR /app

COPY --from=base /app /app

COPY . .

EXPOSE 5000

# CMD ["waitress-serve", "--listen=*:5000", "app:app"]
CMD ["python", "prod-server.py"]

