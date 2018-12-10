import os
import pytest
import docker
import time

from utils import docker_client


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
def start_multi_master(edit_config, start_container, docker_services):
    start_container('master1')
    time.sleep(5)
    start_container('master2')
    time.sleep(5)
    start_container('minion1', cmd=['salt-call', 'test.ping'])
    time.sleep(5)
    edit_config('minion1', '/etc/salt/minion',
                'master_type: failover\nmaster_alive_interval: 10', 'salt-minion')
    yield
    docker_services.shutdown()

def test_multi_master_failover(start_multi_master):
    '''
    test multi-master failover when both masters are running
    only master1 should return miniong communication
    '''
    master1 = docker_client('master1')
    ret = master1.exec_run('salt * test.ping')
    assert ret.exit_code == 0
    assert b'True' in ret.output

    master2 = docker_client('master2')
    ret = master2.exec_run('salt * test.ping')
    assert ret.exit_code == 1
    assert b'Minions returned with non-zero' in ret.output

def test_multi_master_failover_stop_master(start_multi_master):
    '''
    test multi-master failover when both masters are running
    then kill connected master and minion should migrate to
    the other master
    '''
    master1 = docker_client('master1')
    ret = master1.exec_run('salt * test.ping')
    assert ret.exit_code == 0
    assert b'True' in ret.output

    master2 = docker_client('master2')
    ret = master2.exec_run('salt * test.ping')
    assert ret.exit_code == 1
    assert b'Minions returned with non-zero' in ret.output

    master1.exec_run('pkill salt-master')
    time.sleep(40)

    ret = master2.exec_run('salt * test.ping')
    assert ret.exit_code == 0
    assert b'True' in ret.output

    ret = master1.exec_run('salt * test.ping')
    assert b'The master is not responding' in ret.output

def test_multi_master_failover_stop_second_master(start_multi_master):
    '''
    test multi-master failover when first master is running
    and second is not on startup of minion
    '''
    master2 = docker_client('master2')
    master2.exec_run('pkill salt-master')

    minion1 = docker_client('minion1')
    minion1.exec_run('pkill salt-minion')
    minion1.exec_run('salt-minion -d')
    time.sleep(20)

    ret = master2.exec_run('salt * test.ping')
    assert b'The master is not responding' in ret.output

    master1 = docker_client('master1')
    ret = master1.exec_run('salt * test.ping')
    assert ret.exit_code == 0
    assert b'True' in ret.output

    master2.exec_run('salt-master -d')
    time.sleep(60)
    master1.exec_run('pkill salt-master')
    time.sleep(60)

    ret = master2.exec_run('salt * test.ping')
    assert ret.exit_code == 0
    assert b'True' in ret.output

    ret = master1.exec_run('salt * test.ping')
    assert b'The master is not responding' in ret.output

# marking xfail until this issue is fixed: 50791
@pytest.mark.xfail
def test_multi_master_failover_restart_both_masters(start_multi_master):
    '''
    test multi-master failover when both masters are restarted
    '''
    master1 = docker_client('master1')
    master2 = docker_client('master2')
    ret = master1.exec_run('salt * test.ping')
    assert ret.exit_code == 0
    assert b'True' in ret.output

    ret = master2.exec_run('salt * test.ping')
    assert b'Minions returned with non-zero' in ret.output

    # kill both masters
    for master in [master1, master2]:
        master.exec_run('pkill salt-master')

    time.sleep(100)

    for master in [master1, master2]:
        master.exec_run('salt-master -d')

    time.sleep(100)

    ret = master1.exec_run('salt * test.ping')
    assert ret.exit_code == 0
    assert b'True' in ret.output

def test_multi_master_failover_stop_first_master(start_multi_master):
    '''
    test multi-master failover when first master is
    down on startup of minion
    '''
    # stop master1 and restart minion1
    master1 = docker_client('master1')
    master1.exec_run('pkill salt-master')
    minion1 = docker_client('minion1')
    minion1.exec_run('pkill salt-minion')
    minion1.exec_run('salt-minion -d')
    time.sleep(40)

    master2 = docker_client('master2')
    ret = master2.exec_run('salt * test.ping')
    assert ret.exit_code == 0
    assert b'True' in ret.output

    ret = master1.exec_run('salt * test.ping')
    assert b'The master is not responding' in ret.output

# marking xfail until this issue is fixed: 50791
@pytest.mark.xfail
def test_multi_master_failover_masters_stopped_on_start(start_multi_master):
    '''
    test multi-master failover when both masters are stopped
    on start of minion. later on start master and make sure minion
    re-connects
    '''
    # stop master1 and restart minion1
    master1 = docker_client('master1')
    master2 = docker_client('master2')
    minion1 = docker_client('minion1')
    for x,y in {master1: 'master', master2: 'master', minion1: 'minion'}.items():
        x.exec_run('pkill salt-{0}'.format(y))

    # start minion
    minion1.exec_run('salt-minion -d')
    time.sleep(200)

    for master in [master1, master2]:
        ret = master.exec_run('salt * test.ping')
        assert b'The master is not responding' in ret.output

    master2.exec_run('salt-master -d')
    time.sleep(40)
    ret = master2.exec_run('salt * test.ping')
    assert ret.exit_code == 0
    assert b'True' in ret.output
