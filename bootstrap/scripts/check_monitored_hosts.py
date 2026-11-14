#!/usr/bin/env python3
"""Verify that the monitoring core monitors every enabled device.

Usage:
    check_monitored_hosts.py <livestatus socket> <inventory file>

The script queries the Livestatus API of the core, compares the known hosts
with the enabled devices from the Git inventory and exits with 0 when every
enabled device is monitored.
"""

import json
import socket
import sys

import yaml


def query_hosts(socket_path):
    """Return the host table of the core as a list of rows."""
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(15)
    try:
        connection.connect(socket_path)
        connection.sendall(b"GET hosts\nOutputFormat: json\n")
        chunks = []
        while True:
            data = connection.recv(65536)
            if not data:
                break
            chunks.append(data)
    finally:
        connection.close()
    payload = b"".join(chunks).decode("utf-8").strip()
    return json.loads(payload) if payload else []


def enabled_devices(inventory_path):
    """Return the ids of the devices that are enabled in the inventory."""
    with open(inventory_path, "r", encoding="utf-8") as handle:
        inventory = yaml.safe_load(handle)
    return [
        device["id"]
        for device in inventory.get("devices", [])
        if device.get("enabled")
    ]


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    rows = query_hosts(sys.argv[1])
    if not rows:
        print("Livestatus returned no hosts")
        return 1
    header = rows[0]
    if "name" not in header:
        print("Unexpected Livestatus response, the name column is missing")
        return 1
    index = header.index("name")
    names = sorted(row[index] for row in rows[1:])
    print("Hosts known to the core: {0}".format(", ".join(names)))
    expected = enabled_devices(sys.argv[2])
    missing = [name for name in expected if name not in names]
    if missing:
        print("Enabled devices missing from the core: {0}".format(", ".join(missing)))
        return 1
    print("All {0} enabled devices are monitored".format(len(expected)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
