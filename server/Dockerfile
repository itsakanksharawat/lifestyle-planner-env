<<<<<<< HEAD
FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r server/requirements.txt

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
=======
FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn pydantic

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
>>>>>>> 6d39c54215ae40124371e71bc5c5390de8d5fe7e
