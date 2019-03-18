FROM salt-multi-master-image
ARG TRANSPORT

ADD master /etc/salt/master
ADD master_minion.pem /etc/salt/pki/master.pem
ADD master_minion.pub /etc/salt/pki/master.pub
ADD master_minion.pem /etc/salt/pki/minion/minion.pem
ADD master_minion.pub /etc/salt/pki/minion/minion.pub
ADD master_minion.pub /etc/salt/pki/minion/minion_master.pub
ADD minion1.pub /etc/salt/pki/master/minions/minion1

RUN if [[ ${TRANSPORT} == 'tcp' ]]; then salt-call --local file.append /etc/salt/master "transport: ${TRANSPORT}"; fi

RUN ln -sf /usr/lib/systemd/system/salt-master.service /etc/systemd/system/multi-user.target.wants/salt-master.service
#RUN salt-run salt.cmd tls.create_self_signed_cert
