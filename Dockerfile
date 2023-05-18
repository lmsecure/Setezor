FROM python:3.8.14-slim-buster
RUN apt update && apt install -y nmap python3-pip net-tools
COPY ./src/requirements.txt ./
RUN pip3 install -r requirements.txt
COPY ./src/ /lms.netmap/
WORKDIR /lms.netmap/
ENTRYPOINT ["python3", "./app.py"]
