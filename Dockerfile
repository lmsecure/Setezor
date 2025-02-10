FROM debian:trixie-slim
RUN apt update
WORKDIR /
COPY setezor_*.deb setezor.deb
RUN apt install ./setezor.deb -y
ENTRYPOINT ["setezor"]