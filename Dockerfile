FROM python:3.13-slim AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y git
WORKDIR /app
COPY setezor/requirements.txt .
RUN python3 -m pip install --prefix=/install --no-cache-dir --root-user-action=ignore -r requirements.txt
COPY setezor setezor

FROM python:3.13-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --from=builder /app /app
CMD ["python3", "setezor/setezor.py"]
