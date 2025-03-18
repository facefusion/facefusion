FROM python:3.12

ARG FACEFUSION_VERSION=3.1.1
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV PIP_BREAK_SYSTEM_PACKAGES=1

WORKDIR /workspace/backend
COPY . .

RUN apt-get update
RUN apt-get install curl -y
RUN apt-get install ffmpeg -y

EXPOSE 8000

RUN python install.py --onnxruntime default --skip-conda
RUN python facefusion.py force-download