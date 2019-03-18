======================
Salt Multi Master Demo
======================

A Salt Multi Master Demo using Docker.


Instructions
============

Run the following commands in a terminal. Git, Docker, and Docker Compose need
to already be installed.

.. code-block:: bash

    git clone https://github.com/gtmanfred/salt-docker-demo.git
    cd salt-docker-demo/multi_master/
    docker build --build-arg salt_version=v2018.3.3 . -t salt-multi-master-image --no-cache
    docker-compose -f docker-compose.yml build --no-cache
    docker-compose up -d
