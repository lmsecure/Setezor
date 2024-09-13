FROM python:3.12-slim
RUN apt update && apt install -y nmap masscan net-tools python3-pip
COPY ./setezor/requirements.txt ./
RUN pip3 install -r requirements.txt
COPY ./setezor/ /setezor/
WORKDIR /
EXPOSE 16661
ENV APPIMAGE=/setezor/
ENTRYPOINT ["python3", "setezor/setezor.py"]
