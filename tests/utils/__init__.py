import docker

def docker_client(host):
    client = docker.from_env()
    salt_host = client.containers.list(filters={'name': host})[0]
    return salt_host
