FROM python:3

RUN mkdir /code
WORKDIR /code

RUN apt update \
  && apt -y install \
    open-jtalk \
    open-jtalk-mecab-naist-jdic \
    alsa-utils \
    mpg123

ADD requirements.txt /code/
RUN pip install -r requirements.txt
