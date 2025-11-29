FROM openjdk:21-slim-bullseye

# 拷贝程序和启动脚本至根目录
COPY ./src /app
COPY ./service/docker-entrypoint.sh /docker-entrypoint.sh

EXPOSE 8080

# 指定容器入口点
ENTRYPOINT [ "/bin/bash","/docker-entrypoint.sh" ]
