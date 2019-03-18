FROM salt-multi-master-image
ARG TRANSPORT

ADD minion1 /etc/salt/minion
ADD minion1.pem /etc/salt/pki/minion/minion.pem
ADD minion1.pub /etc/salt/pki/minion/minion.pub

RUN if [[ ${TRANSPORT} == 'tcp' ]]; then salt-call --local file.append /etc/salt/minion "transport: ${TRANSPORT}"; fi
