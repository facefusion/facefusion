FROM python:3.10

RUN mkdir app
WORKDIR app

ADD . /app/

RUN apt-get update
RUN apt-get install curl -y
RUN apt-get install ffmpeg -y

RUN pip install -r requirements.txt

RUN python install.py --onnxruntime default --skip-conda

CMD python main.py
