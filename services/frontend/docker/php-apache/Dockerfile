FROM php:8.0-apache
RUN docker-php-ext-install mysqli


ARG FASTAPI_URL
ENV FASTAPI_URL=${FASTAPI_URL}

RUN a2enmod rewrite
