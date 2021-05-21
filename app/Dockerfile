FROM ubuntu:18.04

RUN apt-get update -y && apt-get install -y python3-pip python3-dev git gcc dos2unix g++

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip3 install --upgrade pip
RUN pip3 install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.0.0/en_core_web_sm-3.0.0.tar.gz --user
RUN pip3 install -r requirements.txt

COPY . /app/

RUN dos2unix app/boot.sh && apt-get --purge remove -y dos2unix
RUN chmod +x app/boot.sh

ENV LC_ALL=en_CA.UTF-8
ENV LANG=en_CA.UTF-8
ENV LANGUAGE=en_CA.UTF-8

EXPOSE 5000

ENTRYPOINT ["python3"]