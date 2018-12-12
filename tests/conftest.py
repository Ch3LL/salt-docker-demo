import docker
import os
import pytest
import time

from utils import docker_client

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

        return True
    return _start_salt_host

@pytest.fixture()
def edit_config():
    def _edit_salt_config(salt_host, conf, content, service):
        '''
        edit a salt config and restart service
        '''
        host = docker_client(salt_host)
        host.exec_run('pkill {0}'.format(service))
        host.exec_run('salt-call --local file.append {0} "{1}"'.format(conf, content))
        host.exec_run('{0} -d'.format(service))
        time.sleep(100)
    return _edit_salt_config

@pytest.fixture('module')
def build_image():
    def _build_salt_image(name, path, buildargs):
        client = docker.from_env()
        ret = client.images.build(path=path, tag=name, buildargs=buildargs,
                                  nocache=True)
    return _build_salt_image
