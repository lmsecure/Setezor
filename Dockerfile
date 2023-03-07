FROM python:3.8.14-slim-buster
RUN apt update && apt install -y nmap python3-pip net-tools
COPY ./requirements.txt ./
RUN pip install -r requirements.txt
COPY ./ /lms.netmap/
WORKDIR /lms.netmap/
ENTRYPOINT ["python3", "./app.py"]
