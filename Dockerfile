FROM python:3.13.3

ENV HOME=/home/dude \
    PROJECT_DIR=/home/dude/bms_service \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

RUN mkdir -p $PROJECT_DIR \
    && groupadd -r dude \
    && useradd -r -g dude dude \
    && apt update && apt upgrade -y && apt autoremove -y \
    && apt install curl \
    && rm -rf /var/lib/apt/lists/*


RUN mkdir -p $PROJECT_DIR/log

WORKDIR $PROJECT_DIR

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r ./requirements.txt \
    && chown -R dude:dude $HOME

COPY . .

RUN chown -R dude:dude $PROJECT_DIR

USER dude
