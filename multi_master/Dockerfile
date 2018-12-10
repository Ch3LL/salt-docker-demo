FROM centos/systemd

RUN curl -o /bootstrap -Ls https://bootstrap.saltstack.com
RUN bash /bootstrap -MPX -p pyOpenSSL -c /tmp -g https://github.com/ch3ll/salt.git git fluorine

RUN echo 'tmpfs /run tmpfs rw,nosuid,nodev,mode=755 0 0' >> /etc/fstab
