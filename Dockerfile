FROM ubuntu:24.04
RUN apt update
WORKDIR /
COPY setezor_*.deb setezor.deb
RUN apt install ./setezor.deb -y
ENTRYPOINT ["setezor"]