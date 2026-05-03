#!/usr/bin/env python3
"""
Splunk Deployment Server — Client Status Reporter
===================================================
Generates a report of all connected forwarder clients,
their last check-in time, installed apps, and status.

Usage:
    python3 client_status.py --output report.csv
    python3 client_status.py --stale-threshold 24  # hours
"""

import argparse
import csv
import json
import sys
import urllib.request
import urllib.parse
import ssl
from datetime import datetime, timedelta

class DeploymentServerClient:
    """Interface to the Splunk Deployment Server REST API."""

    def __init__(self, host='localhost', port=8089, token=None):
        self.base_url = f'https://{host}:{port}'
        self.token = token
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def _request(self, endpoint, params=None):
        """Make authenticated request to Splunk REST API."""
        url = f'{self.base_url}{endpoint}'
        if params:
            url += '?' + urllib.parse.urlencode(params)

        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {self.token}')
        req.add_header('Content-Type', 'application/json')

        with urllib.request.urlopen(req, context=self.ssl_context) as resp:
            return json.loads(resp.read().decode())

    def get_clients(self):
        """Retrieve all deployment clients."""
        params = {'output_mode': 'json', 'count': 0}
        data = self._request(
            '/services/deployment/server/clients', params
        )
        return data.get('entry', [])

    def get_server_classes(self):
        """Retrieve all server class definitions."""
        params = {'output_mode': 'json', 'count': 0}
        data = self._request(
            '/services/deployment/server/serverclasses', params
        )
        return data.get('entry', [])

    def get_applications(self):
        """Retrieve all deployment applications."""
        params = {'output_mode': 'json', 'count': 0}
        data = self._request(
            '/services/deployment/server/applications', params
        )
        return data.get('entry', [])


def generate_report(clients, stale_hours=24):
    """Process client data and generate status report."""
    now = datetime.utcnow()
    stale_threshold = now - timedelta(hours=stale_hours)
    report = []

    for client in clients:
        content = client.get('content', {})
        last_phone_home = content.get('lastPhoneHomeTime', 'Unknown')

        # Determine status
        status = 'Active'
        if last_phone_home != 'Unknown':
            try:
                last_time = datetime.strptime(
                    last_phone_home, '%a %b %d %H:%M:%S %Y'
                )
                if last_time < stale_threshold:
                    status = 'Stale'
            except ValueError:
                status = 'Unknown'

        report.append({
            'hostname': content.get('hostname', 'N/A'),
            'ip': content.get('ip', 'N/A'),
            'dns': content.get('dns', 'N/A'),
            'machine_type': content.get('machineType', 'N/A'),
            'splunk_version': content.get('splunkVersion', 'N/A'),
            'last_phone_home': last_phone_home,
            'status': status,
            'server_classes': ', '.join(
                content.get('serverClasses', [])
            ),
            'apps_installed': content.get('applicationCount', 0),
        })

    return report


def write_csv(report, output_file):
    """Write report to CSV file."""
    if not report:
        print("No clients found.")
        return

    fieldnames = report[0].keys()
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report)

    print(f"Report written to {output_file} ({len(report)} clients)")


def print_summary(report):
    """Print summary statistics."""
    total = len(report)
    active = sum(1 for r in report if r['status'] == 'Active')
    stale = sum(1 for r in report if r['status'] == 'Stale')
    unknown = sum(1 for r in report if r['status'] == 'Unknown')

    print("\n" + "=" * 50)
    print("  Deployment Server Client Summary")
    print("=" * 50)
    print(f"  Total Clients:   {total}")
    print(f"  Active:          {active}")
    print(f"  Stale:           {stale}")
    print(f"  Unknown:         {unknown}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description='Splunk Deployment Server Client Status Reporter'
    )
    parser.add_argument('--host', default='localhost',
                       help='DS hostname (default: localhost)')
    parser.add_argument('--port', default=8089, type=int,
                       help='DS management port (default: 8089)')
    parser.add_argument('--token', required=True,
                       help='Splunk auth token')
    parser.add_argument('--output', default='client_status_report.csv',
                       help='Output CSV file path')
    parser.add_argument('--stale-threshold', default=24, type=int,
                       help='Hours before client is considered stale')

    args = parser.parse_args()

    ds = DeploymentServerClient(args.host, args.port, args.token)
    clients = ds.get_clients()
    report = generate_report(clients, args.stale_threshold)
    print_summary(report)
    write_csv(report, args.output)


if __name__ == '__main__':
    main()
