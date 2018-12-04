import docker
import os
import pytest
import time


@pytest.fixture(scope='function')
def start_container(docker_services):
    def _start_salt_host(salt_host, cmd=None):
        docker_services.start(salt_host)
        # run a command to verify a service is running
        if cmd:
            if not isinstance(cmd, list):
                raise Exception('cmd is required to be a list')
            t_stop = time.time() + 60 * 1
            while time.time() < t_stop:
                time.sleep(5)
                ret = docker_services.exec(salt_host, *cmd)
                if 'True' in ret:
                    break
            if 'True' not in ret:
                raise Exception('Service on {0} did not start'.format(salt_host))

        # get docker container id
        client = docker.from_env()
        salt_host = client.containers.list(filters={'name': salt_host})[0]
        return salt_host
    return _start_salt_host
