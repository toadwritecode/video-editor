FROM python:3.10-slim-bullseye

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /src
ADD /requirements.txt /src/requirements.txt
RUN pip3 install -r requirements.txt
COPY /src /src
COPY /model /src/model