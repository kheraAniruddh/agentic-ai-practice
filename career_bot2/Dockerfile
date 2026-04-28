FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -U pip setuptools
RUN pip install --no-cache-dir .

EXPOSE 7860

ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD ["python", "app.py"]