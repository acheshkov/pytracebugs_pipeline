FROM ubuntu:20.04

RUN useradd anomaly --uid 10000

RUN apt update
RUN apt install -y python3
RUN apt install -y python3-pip
RUN apt install --no-install-recommends -y git
RUN apt install -y python3-requests

ENV DEBIAN_FRONTEND noninteractive
RUN apt install --no-install-recommends -y python3-pandas

RUN pip3 install tree-sitter
RUN pip3 install GitPython
RUN pip3 install pickle5
RUN pip3 install torch
RUN pip3 install transformers

WORKDIR /home/anomaly

COPY code_item.py code_storage.py file_utils.py parse_utils.py \
     code_corpus.py ml_utils.py representator.py utils.py \
     code_representation.py anomalist.py dataloader.py vae.py \
     anomalist_data/vae_214_995415.pth anomalist_data/scaler_214_995415.pickle \
     empty.py /home/anomaly/

RUN python3 -c 'import parse_utils; parse_utils.build_tree_sitter_lib(".", "langs_py_java_csharp.so")'
COPY prototype.py /home/anomaly/

RUN python3 /home/anomaly/prototype.py empty.py

CMD python3 /home/anomaly/prototype.py
