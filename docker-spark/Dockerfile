
FROM apache/spark:3.5.1

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-pip \
        python3-dev \
        build-essential \
        vim \
        nano \
        bash-completion && \
    pip3 install --no-cache-dir \
        jupyterlab \
        pyspark==3.5.1 \
        numpy \
        pandas \
        ipython && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    echo ". /usr/share/bash-completion/bash_completion" >> /etc/bash.bashrc

# Crear directorios y configurar permisos
RUN mkdir -p \
        /home/spark/jupyter_runtime \
        /home/spark/jupyter_data \
        /home/spark/jupyter_config \
        /opt/spark-notebooks && \
    chown -R spark:spark /home/spark /opt/spark-notebooks

ENV SHELL=/bin/bash

ENV JUPYTER_RUNTIME_DIR=/home/spark/jupyter_runtime
ENV JUPYTER_DATA_DIR=/home/spark/jupyter_data
ENV JUPYTER_CONFIG_DIR=/home/spark/jupyter_config

USER spark

WORKDIR /opt/spark-notebooks

EXPOSE 8888 4040

CMD ["python3", "-m", "jupyterlab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser"]
