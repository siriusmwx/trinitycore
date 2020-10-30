FROM ubuntu:18.04

ARG CMAKE_FLAGS="-DCMAKE_INSTALL_PREFIX=/root"

RUN \
    sed -i s@/archive.ubuntu.com/@/mirrors.163.com/@g /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y git clang cmake make gcc g++ libmysqlclient-dev libssl-dev libbz2-dev libreadline-dev libncurses-dev libboost-all-dev mysql-server p7zip \
    && update-alternatives --install /usr/bin/cc cc /usr/bin/clang 100 \
    && update-alternatives --install /usr/bin/c++ c++ /usr/bin/clang 100

# pull down trinitycore
WORKDIR /root
ADD TrinityCore.tar.gz .

# run the cmake wrapper
RUN \
    mkdir -p "TrinityCore/build" \
    && cd "TrinityCore/build" \
    && cmake ../ ${CMAKE_FLAGS} \
    && make -j4 && make install

# pull down TDB_full_world_335 database and conf
ADD data.tar.gz .
ADD TDB_full_world_335.tar.gz bin
COPY etc/* etc/

# remove the dependencies and clean apt cache
RUN \
    echo "cd /root/bin\n./authserver &\n./worldserver" > start.sh \
    && chmod +x start.sh \
    && service mysql start \
    && cat "TrinityCore/sql/create/create_mysql.sql" | mysql \
    && apt-get purge -y git clang cmake p7zip \
    && apt-get autoremove -y \
    && apt-get clean -y

EXPOSE 3724 8085

ENTRYPOINT service mysql start && /bin/bash
