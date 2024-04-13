FROM python:3.12

WORKDIR /app

COPY ./services/backend/requirements.txt  ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ./services/backend ./backend

ENV LOGURU_COLORIZE "true"

CMD ["python", "-m", "backend.main"]