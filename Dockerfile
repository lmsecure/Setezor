FROM python:3.13-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
WORKDIR /app
COPY setezor/requirements.txt .
RUN python3 -m venv venv
COPY . .
ENV PATH="/app/venv/bin:$PATH"
RUN apt-get install git -y
RUN . venv/bin/activate && python -m pip install --root-user-action=ignore --upgrade pip && \
    pip install --no-cache-dir --root-user-action=ignore -r requirements.txt
CMD ["python3", "setezor/setezor.py"]