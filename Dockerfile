FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r server/requirements.txt

EXPOSE 7860

CMD ["python", "inference.py"]