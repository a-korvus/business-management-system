FROM python:3.13.2

ENV HOME=/home/fast \
    PROJECT_DIR=/home/fast/bms_service \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

RUN mkdir -p $PROJECT_DIR \
    && groupadd -r fast \
    && useradd -r -g fast fast \
    && apt install curl


RUN mkdir -p $HOME/log && chown fast:fast $HOME/log

WORKDIR $HOME

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r ./requirements.txt \
    && chown -R fast:fast $HOME


COPY . .

RUN chown -R fast:fast $PROJECT_DIR

USER fast
