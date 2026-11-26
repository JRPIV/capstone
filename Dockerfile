FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY onboarding onboarding
COPY workspace workspace

ENV ONBOARDING_HOST=0.0.0.0
ENV PORT=8000
ENV ONBOARDING_DB_PATH=/data/onboarding.sqlite
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /data
EXPOSE 8000
CMD ["python", "-m", "onboarding.server"]
