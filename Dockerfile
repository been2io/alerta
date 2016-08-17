FROM ubuntu:latest
RUN apt-get update && apt-get install -y git wget build-essential python python-setuptools python-pip python-dev libffi-dev
COPY . /opt/alerta
WORKDIR /opt/alerta
ENV CORS_ORIGINS *
RUN pip install Flask
RUN python setup.py install
ENTRYPOINT alertad