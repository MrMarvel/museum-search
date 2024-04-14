FROM mysql:8

COPY ./dump.sql /app/dump.sql

RUN cat /app/dump.sql | /usr/bin/mysql -u root --password=ROOT