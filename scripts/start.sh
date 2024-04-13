#!/bin/bash

docker compose up --build -d

cat services/frontend/dump.sql | docker exec -i mysql /usr/bin/mysql -u root --password=ROOT