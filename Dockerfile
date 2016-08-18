FROM ubuntu:latest
RUN apt-get update && apt-get install -y git wget build-essential python python-setuptools python-pip python-dev libffi-dev
COPY . /opt/alerta
WORKDIR /opt/alerta
ENV CORS_ORIGINS *
RUN pip install Flask && \
    python setup.py install && \
    git clone https://github.com/been2io/angular-alerta-webui.git /opt/alertaUI
ENV UI_PATH /opt/alertaUI/app
ENTRYPOINT alertad