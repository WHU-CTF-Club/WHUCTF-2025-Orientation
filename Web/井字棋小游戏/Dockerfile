FROM python:3.12-slim-bookworm

# apt更换镜像源，并更新软件包列表信息
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update && \
    apt install patch gcc wget unzip gosu iptables -y

# 安装必要的python依赖库
RUN python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    setuptools Flask

COPY ./src /app
COPY ./service /

WORKDIR /app

EXPOSE 8080

ENTRYPOINT ["/bin/bash","/docker-entrypoint.sh"]
