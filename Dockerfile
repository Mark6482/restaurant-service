FROM python:3.11

WORKDIR /app

COPY requirements/prod.txt .

RUN pip install --no-cache-dir -r prod.txt

COPY src/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]