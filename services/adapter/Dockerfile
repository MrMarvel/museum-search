FROM python:3.11

COPY ./services/adapter/requirements.txt ./
RUN pip3 install -r requirements.txt

WORKDIR /app

COPY ./services/adapter adapter/
COPY ./configs configs/

ENV LOGURU_COLORIZE "true"

CMD ["python", "-m", "adapter"]