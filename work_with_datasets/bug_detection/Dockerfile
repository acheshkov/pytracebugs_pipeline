FROM ubuntu:20.04

RUN useradd bug_detection --uid 10000

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
RUN pip3 install lightgbm==2.2.3
RUN pip3 install torch
RUN pip3 install transformers

WORKDIR /home/bug_detection

COPY code_item.py code_storage.py file_utils.py parse_utils.py \
     code_corpus.py ml_utils.py representator.py utils.py \
     models/clf_lgb_1M_stable_vs_14k_bugs_351338s_14089b.joblib \
     empty.py /home/bug_detection/

RUN python3 -c 'import parse_utils; parse_utils.build_tree_sitter_lib(".", "langs_py_java_csharp.so")'
COPY prototype.py /home/bug_detection/

RUN python3 /home/bug_detection/prototype.py empty.py

CMD python3 /home/bug_detection/prototype.py
