FROM python:3.10-slim-bullseye

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1


COPY /src /src
RUN pip3 install --upgrade pip
RUN pip3 install -r /src/requirements.txt
WORKDIR /src