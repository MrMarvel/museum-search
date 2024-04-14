FROM python:3.12

WORKDIR /app

COPY ./services/backend/requirements.txt  ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ./services/backend ./backend
COPY ./configs ./configs

ENV LOGURU_COLORIZE "true"

ARG DEFAULT_WEBHOOK_URL
ENV DEFAULT_WEBHOOK_URL=${DEFAULT_WEBHOOK_URL}

EXPOSE 8102

CMD ["python", "-m", "backend.main"]