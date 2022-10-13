FROM python:3.8.14-slim-buster
COPY ./requirements.txt ./
RUN apt update && apt install -y nmap python3-pip net-tools
RUN pip install -r requirements.txt
COPY ./ /network_topology/
WORKDIR /network_topology/
ENTRYPOINT ["python3", "./app.py"]
