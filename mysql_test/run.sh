#!/usr/bin/bash

docker run -d \
	-p 3306:3306 \
	-v ./etc/mysql:/etc/mysql/mysql.conf.d/ \
	-v ./data/mysql:/var/lib/mysql \
	-e MYSQL_ROOT_PASSWORD=root \
	--name mysql \
	mysql:latest
