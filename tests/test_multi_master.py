import os
import pytest
import docker
import time

@pytest.fixture(scope='session')
def docker_compose_files(pytestconfig):
    '''
    specify docker-compose.yml if not in tests directory
    '''
    root_dir = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
    return [
        os.path.join(root_dir, 'multi_master', 'docker-compose.yml'),
    ]

@pytest.fixture(scope='function')
def start_multi_master(start_container, docker_services):
    start_container('master1')
    time.sleep(5)
    start_container('master2')
    time.sleep(5)
    start_container('minion1', cmd=['salt-call', 'test.ping'])
    time.sleep(5)
    yield
    docker_services.shutdown()

def _docker_client(host):
    client = docker.from_env()
    salt_host = client.containers.list(filters={'name': host})[0]
    return salt_host

def test_multi_master(start_multi_master):
    '''
    test multi-master when both masters are running
    '''
    for master in ['master1', 'master2']:
        salt_host = _docker_client(master)
        ret = salt_host.exec_run('salt \* test.ping')
        assert ret.exit_code == 0

def test_multi_second_master(start_multi_master):
    '''
    test first master stopped and run cmds from second
    '''
    master1 = _docker_client('master1')
    master1.exec_run('pkill salt-master')

    master2 = _docker_client('master2')
    ret = master2.exec_run('salt \* test.ping')
    assert ret.exit_code == 0
