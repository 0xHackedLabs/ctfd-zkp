FROM python:3.9.13

ENV HTTP_PORT=31337

RUN true \
    && apt update \
    && apt install -y tini \
    && rm -rf /var/cache/apt/archives \
    && useradd -m ctf \
    && true

COPY requirements.txt /root
RUN python3 -m pip install -r /root/requirements.txt 
RUN true \
    && curl -L https://foundry.paradigm.xyz | bash \
    && bash -c "source /root/.bashrc && foundryup" \
    && chmod 755 -R /root \
    && true

COPY start.py /home/ctf/start.py
ENTRYPOINT ["tini", "-g", "--"]

WORKDIR /home/ctf
CMD ["python3", "start.py"]