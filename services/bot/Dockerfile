FROM python:3.10

COPY ./services/bot/requirements.txt ./
RUN pip3 install -r requirements.txt

WORKDIR /app

COPY ./services/bot ./bot

ENV LOGURU_COLORIZE "true"

CMD ["python", "-m", "bot"]