FROM python:3.10

WORKDIR /app

COPY ./services/backend/requirements.txt  ./

RUN pip install -r requirements.txt

COPY ./services/backend ./backend
COPY ./services/rabbit ./rabbit
COPY ./configs ./configs

ENV LOGURU_COLORIZE "true"

CMD ["python", "-m", "backend"]