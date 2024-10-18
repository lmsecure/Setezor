FROM ubuntu:24.04
RUN apt update && apt install -y nmap masscan net-tools python3-pip python3.12 git
COPY ./setezor/requirements.txt ./
RUN pip3 install -r requirements.txt --break-system-packages
RUN playwright install firefox
RUN playwright install-deps
COPY ./setezor/ /setezor/
WORKDIR /
EXPOSE 16661
ENV APPIMAGE=/setezor/
ENTRYPOINT ["python3", "setezor/setezor.py"]