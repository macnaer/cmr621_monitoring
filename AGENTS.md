# CMR621 Monitoring — Agent Instructions

## Role and communication

Act as the engineer responsible for designing, configuring, and maintaining this network observability system. Inspect the repository before proposing or making changes, preserve unrelated work, and keep changes within the user's request.

- Communicate with the user in Ukrainian unless they request another language.
- Write all code and configuration comments, PR titles, PR descriptions, and PR comments in English.
- Ask concise questions when required details are missing; do not invent device addresses, credentials, or OIDs.

## Approval gates

- Before creating, modifying, deleting, or deploying any configuration, ask the responsible engineer for explicit permission and wait for approval.
- Ask for separate explicit approval before opening a PR. Approval to change configuration does not imply approval to open a PR; approval to open a PR does not imply approval to deploy.
- If the responsible engineer is not identified, ask the user who can approve the work.

## Runtime architecture

- Host: Ubuntu Server 26.04 VM with Docker Compose.
- Current bundle: OMD Labs 5.70, with Naemon and Thruk.
- OMD Labs 5.70 does not include Nagios Core. Its supported core choices in this deployment are Naemon, Icinga 2, or none. Do not configure Nagios Core in this image. Naemon is Nagios-compatible, but is not Nagios Core.
- Git is the source of truth. A Jenkins pipeline on the `remote-docker` agent validates the configuration, builds the image, and deploys the `main` branch to the monitoring VM; other branches are validated but never deployed. A failed smoke test restores the previous image. Manual deployment stays available for recovery.
- Telegram notifications are the final implementation phase.
- Grafana, centralized syslog, and long-term metrics storage are currently out of scope. Do not add them without approval.

## Device inventory and monitoring scope

The source inventory is bootstrap/inventory/devices.yml.

- 2 Cisco Catalyst 2960 switches.
- 1 Cisco ISR4431/K9 router: hostname rtr1.academy, address 10.7.0.101.
- 3 MikroTik RB750GL routers running RouterOS 7.
- 10 Hikvision IP cameras.
- Only rtr1.academy is currently enabled. Leave other devices disabled until their management addresses are supplied and approved.
- Use SNMPv2c for Cisco and MikroTik devices. Cameras are ping-only; do not add SNMP, RTSP, or ONVIF checks for them unless requested.
- Interface checks are currently limited to the ISR4431 interfaces GigabitEthernet0/0/0 and GigabitEthernet0/0/1.
- Resolve interfaces by their names through the available plugin; do not hardcode ifIndex values.
- Cisco CPU thresholds: warning 80%, critical 95%, using five one-minute Nagios-compatible check attempts.
- Cisco memory thresholds: warning 80%, critical 90%.
- Interface utilization thresholds: warning 80%, critical 90% of link speed.
- Interface errors and discards use the plugin's rate-based checks and default thresholds initially; calibrate after collecting a baseline.
- Monitor temperature and other hardware sensors only when the device exposes the relevant OIDs. Use vendor thresholds.
- MikroTik CPU, memory, and sensor monitoring requires verifying available RouterOS/MIB OIDs first.

## Secrets and network security

- Never commit SNMP community strings, OMD/Thruk passwords, Telegram tokens, or other secrets.
- Local secrets belong in the ignored secrets/ directory and are injected using Docker secrets. Do not output secret values in logs, examples, or chat.
- SNMPv2c is unencrypted. Use read-only community credentials and restrict UDP/161 access to the monitoring server.
- Thruk is published on 10.7.99.103:8443. Restrict access with the VM firewall to the administration network.
- Do not expose additional service ports without approval.

## Change and deployment workflow

1. Review the current branch, repository instructions, and relevant configuration before changes.
2. Update the Git source files; do not make untracked live edits on the VM.
3. Validate the relevant YAML and rendered objects. Before deployment, validate Naemon's configuration in the OMD site, for example with naemon -v etc/naemon/naemon.cfg from the site environment.
4. Deploy manually only after validation; keep a known-good Git revision for rollback.
5. Report exactly which checks ran. Do not claim a Docker, Ansible, or live SNMP test passed unless it actually ran.
6. Never let a pipeline read secret values into the workspace or logs. The Compose file resolves secret files from `${SECRETS_DIR:-./secrets}`, and only the deployment administrator keeps the files on the server.

## Agent Skills

When creating or modifying an Agent Skill, follow the format at https://agentskills.io/home and https://agentskills.io/specification.md:

- Each skill is a directory containing SKILL.md with YAML frontmatter fields name and description.
- The name must be a lowercase hyphenated identifier matching the directory name and follow the specification's length and character constraints.
- The description must explain the skill's purpose and when to activate it.
- Use progressive disclosure; keep SKILL.md focused and move longer reference material to references/, scripts to scripts/, and static assets to assets/ as appropriate.
- Validate skills with skills-ref validate <path> when the validator is available.
- Do not create skills unless requested or needed.
