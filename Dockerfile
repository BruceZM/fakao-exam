FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
COPY server/ ./server/
COPY app/data/questions.json ./app/data/questions.json
RUN mkdir -p /mnt/workspace/fakao-exam && chmod 777 /mnt/workspace/fakao-exam
ENV PORT=7860
ENV ANALYTICS_DB_PATH=/mnt/workspace/fakao-exam/visitor_stats.db
EXPOSE 7860
CMD ["sh","-c","uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
