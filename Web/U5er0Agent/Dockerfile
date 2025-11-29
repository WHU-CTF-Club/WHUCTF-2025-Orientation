FROM php:7.4-fpm-alpine

# 安装必要的软件包
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories && \
    apk add --update --no-cache tar nginx mysql mysql-client bash git libzip-dev

# 配置mysql
RUN docker-php-source extract && \
    docker-php-ext-install pdo_mysql mysqli zip && \
    docker-php-source delete
# 复制nginx+mysql配置文件
COPY ./config/nginx.conf /etc/nginx/nginx.conf

# 复制web项目源码
COPY src /var/www/html

# 重新设置源码路径的用户所有权
RUN chown -R www-data:www-data /var/www/html


# 拷贝容器入口点脚本
COPY ./service/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh


# 设置shell的工作目录
WORKDIR /var/www/html

USER www-data

USER root

EXPOSE 80

# 设置nginx日志保存目录
VOLUME ["/var/log/nginx"]

# 设置容器入口点
ENTRYPOINT [ "/docker-entrypoint.sh" ]
