# CMR621 Network Monitoring

Initial Docker-based implementation for the CMR621 network monitoring system.

## Stack

- Host: Ubuntu Server 26.04 VM with Docker Compose.
- Runtime: OMD Labs 5.70 container, configured to use Naemon and Thruk.
- Configuration source of truth: this Git repository.
- CI: a Jenkins pipeline on the remote-docker agent deploys the main branch to the monitoring VM.
- Notifications: Telegram is intentionally deferred to the final implementation phase.
- Grafana and centralized syslog are out of scope for the current deployment.

The OMD image bundles optional tools, but this project exposes only its HTTPS web endpoint and configures Naemon with Thruk as the default UI. OMD Labs 5.70 does not include Nagios Core; Naemon is the supported Nagios-compatible core in this image. The container is Debian-based; the VM host remains Ubuntu Server 26.04.

## Monitored devices

The inventory is in `bootstrap/inventory/devices.yml`. The Cisco ISR4431 is configured as `rtr1.academy` at `10.7.0.101`. Other device addresses have not been provided, so those entries remain disabled. Do not invent addresses; enable entries only after their addresses are supplied and approved.

- 2 Cisco Catalyst 2960 switches.
- 1 Cisco ISR4431/K9 router.
- 3 MikroTik RB750GL routers running RouterOS 7.
- 10 Hikvision IP cameras.

The current generated configuration supports ICMP host checks and an SNMPv2c uptime service for enabled network devices. Cameras use ICMP only. Cisco devices also receive CPU and memory checks. The enabled ISR4431 receives checks for status, utilization, errors, and discards on the two listed interfaces. MikroTik CPU/memory and hardware sensor checks remain pending validation against the devices' available OIDs.

Only these ISR4431 interfaces are in scope for interface checks:

- `GigabitEthernet0/0/0`
- `GigabitEthernet0/0/1`

Initial thresholds recorded in the inventory:

- CPU: warning 80%, critical 95%, sustained for 5 minutes.
- Memory: warning 80%, critical 90%.
- Interface utilization: warning 80%, critical 90% of link speed.
- Temperature thresholds must come from the device vendor where available.
- Errors and discards are evaluated using the check_nwc_health plugin's rate-based checks and default thresholds; tune these after observing a baseline.
- CPU checks use five one-minute Nagios attempts to avoid alerting on a brief spike.

## Prerequisites

Create two local secret files before starting Compose. Never commit them:

- `secrets/omd_admin_password` — password for the OMD/Thruk administrator.
- `secrets/snmp_community` — the read-only SNMPv2c community configured on the network devices.

The SNMP file contains only the exact community configured on the devices, on one line, without quotes or a `COMMUNITY=` prefix. Example format only — replace this placeholder and do not use it as a real credential:

```text
replace-with-the-existing-read-only-community
```

Generate the administrator password on the Docker VM and save only the password string in the file:

```sh
mkdir -p secrets
openssl rand -base64 36 | tr -d '\n' > secrets/omd_admin_password
chmod 600 secrets/omd_admin_password
```

The file must contain one line with the password itself, without quotes or a variable name. For example, its format is `one-random-password-string` — do not use that literal example as a real password. The SNMP file should likewise contain only the existing read-only community string on one line.

The initial SNMP command uses one shared community for Cisco and MikroTik devices. If their communities differ, add named credential profiles before enabling the affected devices. Use a high-entropy community containing only letters, digits, periods, underscores, or hyphens; SNMPv2c sends it unencrypted on the network.

No credentials are committed. The private management IP for `rtr1.academy` is intentionally recorded in the inventory; SNMP secrets remain in ignored local files.

## Start the stack

The HTTPS port is bound to the Docker server management address `10.7.99.103` on port `8443`. Restrict access to this port with the VM firewall so only the administration network can reach it.

From the repository root:

1. Create the two secret files described above.
2. Run `docker compose build` once to add `htpasswd` (from `apache2-utils`) to the image.
3. Run `docker compose up -d`.
4. Open `https://10.7.99.103:8443/demo/`.

The image uses a self-signed TLS certificate by default, so the browser will show a certificate warning until a trusted certificate/reverse proxy is configured. The named Docker volume `omd-sites` persists OMD configuration and state.

## Configuration workflow without CI

1. Make approved changes in Git; do not edit the live Naemon configuration independently on the VM.
2. On the VM, pull the approved commit.
3. Validate the Naemon configuration before restarting the core: `docker compose exec monitoring su - demo -c 'naemon -v etc/naemon/naemon.cfg'`.
4. Restart the core after a successful validation: `docker compose exec monitoring su - demo -c 'omd restart naemon'`.
5. Review the Thruk UI and container logs.

The OMD startup playbook applies the tracked inventory and configuration when the container starts. Keep a known-good Git commit available for rollback.

## CI/CD with Jenkins

The `Jenkinsfile` in the repository root describes the pipeline. It runs on the `remote-docker` agent, which is the monitoring VM, so the container is rebuilt and restarted in place.

Pipeline stages:

1. Checkout the repository on the agent.
2. Verify the agent: Docker, Docker Compose, and the presence of both secret files.
3. Validate the Compose file and parse the Ansible playbook and inventory YAML.
4. Keep the currently running image as the rollback image.
5. Build the image.
6. Run an Ansible syntax check inside the built image.
7. Deploy with `docker compose -p cmr621_monitoring up -d --force-recreate` (main branch only).
8. Smoke test: container state, OMD status, Naemon configuration validation, and an HTTPS request to the Thruk endpoint.

On a failed smoke test the pipeline restores the rollback image and restarts the container.

### Jenkins job configuration

- Job type: Pipeline, script from SCM.
- SCM: Git, `https://github.com/macnaer/cmr621_monitoring`, branch `main`.
- Trigger: poll the repository on a schedule, for example `*/5 * * * *`. The repository is public, so no credentials are needed.
- The job must be restricted to the `remote-docker` node. The agent user needs membership in the `docker` group and a Docker Compose v2 installation.
- The compose project name is pinned in `compose.yaml` (`name: cmr621_monitoring`) so the `omd-sites` volume keeps its name regardless of the working directory.

### Jenkins workspace

The agent clones the repository into the workspace that Jenkins manages for the job, under the agent remote root (`/home/master/nagios/workspace`). That root must exist and be writable by the agent user, otherwise Jenkins cannot create the job workspace and the checkout fails with `Failed to exec spawn helper`:

```sh
sudo mkdir -p /home/master/nagios/workspace
sudo chown -R master:master /home/master/nagios
```

Do not use the deployment directory that holds the secret files as the workspace. The Git plugin removes untracked files before checkout, which would delete the secrets. The secrets stay in `/home/master/cmr621_monitoring/secrets` and are read from there through `SECRETS_DIR`.
### Secrets during a pipeline run

Secret values stay on the server and are never copied into the workspace or printed. `compose.yaml` reads them from `${SECRETS_DIR:-./secrets}`, and the pipeline sets `SECRETS_DIR=/home/master/cmr621_monitoring/secrets` on the agent. The pipeline only checks that both files exist.

Keep the secret files readable by the deployment administrator only:

```sh
chmod 600 /home/master/cmr621_monitoring/secrets/omd_admin_password
chmod 600 /home/master/cmr621_monitoring/secrets/snmp_community
```


## Current implementation boundary

This bootstrap does not include Telegram, Grafana, syslog, or long-term metrics storage. Only `rtr1.academy` is enabled; other device checks remain disabled pending their management IPs. Temperature/hardware checks will be enabled only after confirming that the devices expose the required sensors. Telegram must be integrated only after the checks and recovery behavior have been accepted.
