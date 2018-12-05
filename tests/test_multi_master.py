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
        ret = salt_host.exec_run('salt * test.ping')
        assert ret.exit_code == 0

def test_multi_first_master(start_multi_master):
    '''
    test first master stopped and run cmds from second
    '''
    for master in ['master1', 'master2']:
        salt_host = _docker_client(master)
        ret = salt_host.exec_run('salt * test.ping')
        assert ret.exit_code == 0

    master1 = _docker_client('master1')
    master1.exec_run('pkill salt-master')

    # make sure master is dead
    ret = master1.exec_run('salt * test.ping')
    assert b'Salt request timed out. The master is not responding' in ret.output

    master2 = _docker_client('master2')
    ret = master2.exec_run('salt * test.ping')
    assert ret.exit_code == 0

def test_multi_second_master(start_multi_master):
    '''
    test second master stopped
    '''
    for master in ['master1', 'master2']:
        salt_host = _docker_client(master)
        ret = salt_host.exec_run('salt * test.ping')
        assert ret.exit_code == 0

    master2 = _docker_client('master2')
    master2.exec_run('pkill salt-master')

    # make sure master is dead
    ret = master2.exec_run('salt * test.ping')
    assert b'Salt request timed out. The master is not responding' in ret.output

    master1 = _docker_client('master1')
    ret = master1.exec_run('salt * test.ping')
    assert ret.exit_code == 0

def test_multi_first_master_down_startup(start_multi_master):
    '''
    test first master down when minion starts up
    '''
    # stop master1 and then start minion1
    master1 = _docker_client('master1')
    master1.exec_run('pkill salt-master')

    # make sure master is dead
    ret = master1.exec_run('salt * test.ping')
    assert b'Salt request timed out. The master is not responding' in ret.output

    minion1 = _docker_client('minion1')
    minion1.exec_run('pkill salt-minion')
    minion1.exec_run('salt-minion -d')
    time.sleep(20)

    master2 = _docker_client('master2')
    ret = master2.exec_run('salt * test.ping')
    assert ret.exit_code == 0

def test_both_masters_stopped(start_multi_master):
    '''
    test when both masters are stopped on minion startup
    '''
    for host in ['master1', 'master2', 'minion1']:
        salt_host = _docker_client(host)
        if 'minion' in host:
            salt_host.exec_run('pkill salt-minion')
        else:
            salt_host.exec_run('pkill salt-master')
            # make sure master is dead
            ret = salt_host.exec_run('salt * test.ping')
            assert b'Salt request timed out. The master is not responding' in ret.output

    # start the minion and let it sit for 5 minutes
    # to make sure it doesnt kill process
    minion1 = _docker_client('minion1')
    minion1.exec_run('salt-minion -d')
    time.sleep(300)

    for master in ['master1', 'master2']:
        salt_host = _docker_client(master)
        salt_host.exec_run('salt-master -d')

    master1 = _docker_client('master1')
    ret = master1.exec_run('salt * test.ping')
    assert ret.exit_code == 0

    master2 = _docker_client('master2')
    ret = master2.exec_run('salt * test.ping')
    assert ret.exit_code == 0

def test_one_master_up_on_startup(start_multi_master):
    '''
    test when one master is up when minion starts up
    '''
    for host in ['master2', 'minion1']:
        salt_host = _docker_client(host)
        if 'minion' in host:
            salt_host.exec_run('pkill salt-minion')
        else:
            salt_host.exec_run('pkill salt-master')

            # make sure master is dead
            ret = salt_host.exec_run('salt * test.ping')
            assert b'Salt request timed out. The master is not responding' in ret.output

    minion1 = _docker_client('minion1')
    minion1.exec_run('salt-minion -d')
    time.sleep(20)

    master1 = _docker_client('master1')
    ret = master1.exec_run('salt * test.ping')
    assert ret.exit_code == 0

    master2= _docker_client('master2')
    salt_host.exec_run('salt-master -d')
    time.sleep(20)

    ret = master2.exec_run('salt * test.ping')
    assert ret.exit_code == 0

def test_refresh_pillar_masters(start_multi_master):
    '''
    test refreshing pillar when masters are up and
    when only one is up
    '''
    # verify both masters are up and can run refresh
    for master in ['master1', 'master2']:
        salt_host = _docker_client(master)
        ret = salt_host.exec_run('salt * saltutil.refresh_pillar')
        assert ret.exit_code == 0

    master1 = _docker_client('master1')
    master1.exec_run('pkill salt-master')

    # make sure master is dead
    ret = master1.exec_run('salt * test.ping')
    assert b'Salt request timed out. The master is not responding' in ret.output

    master2= _docker_client('master2')
    ret = master2.exec_run('salt * saltutil.refresh_pillar')
    assert ret.exit_code == 0

    master2.exec_run('pkill salt-master')

    # make sure master is dead
    ret = master2.exec_run('salt * test.ping')
    assert b'Salt request timed out. The master is not responding' in ret.output

    master1.exec_run('salt-master -d')
    time.sleep(20)
    ret = master1.exec_run('salt * saltutil.refresh_pillar')
    assert ret.exit_code == 0

def test_masters_down_minion_cmd(start_multi_master):
    '''
    test salt-call when both masters are down
    '''
    for master in ['master1', 'master2']:
        salt_host = _docker_client(master)
        ret = salt_host.exec_run('pkill salt-master')
        assert ret.exit_code == 0

    minion1 = _docker_client('minion1')
    ret = minion1.exec_run('salt-call test.ping')
    assert b'No master could be reached' in test.output
