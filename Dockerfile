FROM python:3.8-alpine

WORKDIR /app

# Install Python dependencies
# Ask Ira for help when you need additional build-time dependencies (compilers,
# Fortran libraries, and similar stuff) so he can help you keep the Docker
# image fairly small.
COPY requirements.txt .
RUN apk --no-cache add --virtual .build-deps gcc musl-dev python3-dev libpq-dev\
        && pip --no-cache-dir install -r requirements.txt \
        && apk --no-cache del .build-deps

# Install application code
COPY . .
