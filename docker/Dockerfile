# Monitoring image based on OMD Labs 5.70.
#
# The upstream image does not ship the htpasswd utility that OMD uses to store
# the Thruk administrator password, so the password step in the Ansible
# playbook would fail. apache2-utils provides htpasswd.
FROM consol/omd-labs-debian:v5.70

RUN apt-get update \
    && apt-get install -y --no-install-recommends apache2-utils \
    && rm -rf /var/lib/apt/lists/*