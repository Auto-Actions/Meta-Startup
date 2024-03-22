FROM python:3.10

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        apt-utils \
        build-essential \
        git \
        nano \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /

RUN mkdir -p /app 
# &&\ mkdir -p /app/MetaGPT


COPY . /app
# COPY ./MetaGPT_smart_contract/ /app

WORKDIR /app/MetaGPT_smart_contract/
RUN pip install --no-cache-dir -r requirements.txt &&\
    pip install -e .

WORKDIR /app/fastapi_metagpt_integration

# install torch for GPU version
# RUN pip install -r requirements.txt -f https://download.pytorch.org/whl/lts/1.8/torch_lts.html

RUN pip install -r requirements.txt

# CMD ["uvicorn", "--host", "0.0.0.0", "--port", "5000", "sco.main:app"]
CMD ["python", "-m", "fastapi_metagpt_integration.main"]
