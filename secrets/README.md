# Local secrets

This directory is ignored by Git except for this README. Create the files locally before starting the Compose stack:

- `omd_admin_password`: password for the OMD/Thruk administrator.
- `snmp_community`: the read-only SNMPv2c community configured on all monitored Cisco and MikroTik devices.

The `snmp_community` file must contain only the exact community configured on the devices, on one line, without quotes or a `COMMUNITY=` prefix. Example format only; replace it and do not use it as a real credential:

    replace-with-the-existing-read-only-community

The initial configuration assumes one shared community. The community is stored in the container's runtime Nagios resource file and is never stored in Git. The accepted character set is letters, digits, periods, underscores, and hyphens to prevent shell interpretation in Nagios plugin commands.

Do not paste secret values into chat, commits, issues, or PRs. Restrict local file permissions to the deployment administrator.
