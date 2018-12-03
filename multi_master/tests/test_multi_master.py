import pytest
import docker

@pytest.fixture(scope='session')
def start_container(docker_services):
    def _start_salt_host(salt_host):
        docker_services.start(salt_host)
        client = docker.from_env()
        salt_host = client.containers.list(filters={'name': salt_host})[0]
        return salt_host
    return _start_salt_host

@pytest.fixture(scope='session')
def docker_compose_files(pytestconfig):
    '''
    specify docker-compose.yml if not in tests directory
    '''
    return [
        'docker-compose.yml',
    ]


def test_multi_master(start_container):
    '''
    test multi-master when both masters are running
    '''
    master1 = start_container('master1')
    master2 = start_container('master2')
    minion1 = start_container('minion1')
    import time
    time.sleep(60)

    ret = master1.exec_run('salt \* test.ping')
    assert ret.exit_code == 0
