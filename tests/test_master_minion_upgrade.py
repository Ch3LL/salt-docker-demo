import os
import pytest
import docker
import time

from utils import docker_client

SALT_VERSION='fluorine'

@pytest.fixture(scope='session')
def docker_compose_files(pytestconfig):
    '''
    specify docker-compose.yml if not in tests directory
    '''
    root_dir = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
    return [
        os.path.join(root_dir, 'master_minion', 'docker-compose.yml'),
    ]

@pytest.fixture(scope='function',
                params=['v2016.11.9'])
def start_master_minion(request, build_image, edit_config, start_container, docker_services):
    root_dir = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
    build_image('salt_master_minion',
                os.path.join(root_dir, 'master_minion',
                buildargs={'salt_version': request.param})
    start_container('master1')
    time.sleep(5)
    start_container('minion1', cmd=['salt-call', 'test.ping'])
    time.sleep(5)
    yield
    docker_services.shutdown()

def test_upgrade_versions(request, start_master_minion):
    '''
    test master and minion upgrade
    '''
    # verify initial version works and is correct
    pre_version = ' '.join([x for x in request.keywords.keys() if x.startswith('v20')]).strip('v')
    for version in [pre_version, SALT_VERSION]:
        master1 = docker_client('master1')
        minion1 = docker_client('minion1')
        if version is SALT_VERSION:
            # upgrade
            for salt_host in [master1, minion1]:
                conf = os.path.join('etc', 'salt', 'master')
                if 'minion' in salt_host.name:
                    conf = os.path.join('etc', 'salt', 'minion')

                # add test config
                salt_host.exec_run('salt-call --local file.append {0} "{1}"'.format(conf, 'test_exist: True'))
                ret = salt_host.exec_run('salt-call --local file.contains {0} test_exist'.format(conf))
                assert 'True' in ret
                ret = salt_host.exec_run('bash /bootstrap -MPX -p pyOpenSSL -c /tmp -g https://github.com/ch3ll/salt.git git {0}'.format(SALT_VERSION))
                time.sleep(40)

                # verify config stayed after upgrade
                ret = salt_host.exec_run('salt-call --local file.contains {0} test_exist'.format(conf))
                assert 'True' in ret
        ret = master1.exec_run('salt * test.ping')
        assert ret.exit_code == 0

        ret = master1.exec_run('salt * test.version')
        assert version in str(ret.output)

        ret = master1.exec_run('salt --version')
        assert version in str(ret.output)
