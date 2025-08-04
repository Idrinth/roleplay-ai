#!/usr/bin/env python3

import json
import subprocess
import sys
import argparse
from collections import defaultdict


def get_deployments():
    try:
        result = subprocess.run(
            ['beam', 'deployment', 'list', '--format', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting deployment list: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)


def find_superseded_deployments(deployments, filter_name=None):
    groups = defaultdict(list)
    for deployment in deployments:
        deployment['active'] = deployment.get('active', False)
        groups[deployment['name']].append(deployment)

    if filter_name:
        if filter_name not in groups:
            print(f"No deployments found with name: {filter_name}")
            return []
        groups = {filter_name: groups[filter_name]}

    superseded_ids = []

    for name, group in groups.items():
        group.sort(key=lambda x: x['version'])

        print(f"Processing deployment group: {name}")

        for i, deployment in enumerate(group):
            if not deployment['active']:
                continue

            has_newer_active = any(
                newer['active'] and newer['version'] > deployment['version']
                for newer in group[i + 1:]
            )

            if has_newer_active:
                print(f"  Found superseded: {deployment['id']} (version {deployment['version']})")
                superseded_ids.append(deployment['id'])

    return superseded_ids


def stop_deployment(deployment_id, dry_run=False):
    if dry_run:
        print(f"Would stop deployment: {deployment_id}")
        return True

    try:
        print(f"Stopping deployment: {deployment_id}")
        subprocess.run(
            ['beam', 'deployment', 'stop', deployment_id],
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error stopping deployment {deployment_id}: {e}")
        return False


def list_deployment_names(deployments):
    names = set(deployment['name'] for deployment in deployments)
    print("Available deployment names:")
    for name in sorted(names):
        print(f"  - {name}")


def main():
    parser = argparse.ArgumentParser(description='Stop superseded active deployments')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be stopped without actually stopping'
    )
    parser.add_argument(
        '--name',
        type=str,
        help='Filter by deployment name (process only this deployment)'
    )
    parser.add_argument(
        '--list-names',
        action='store_true',
        help='List all available deployment names and exit'
    )
    args = parser.parse_args()

    print("Retrieving deployment list...")
    deployments = get_deployments()

    if args.list_names:
        list_deployment_names(deployments)
        return

    filter_msg = f" for '{args.name}'" if args.name else ""
    print(f"Finding superseded deployments{filter_msg}...")

    superseded_ids = find_superseded_deployments(deployments, args.name)

    if not superseded_ids:
        print("No superseded deployments found.")
        return

    print(f"Found {len(superseded_ids)} superseded deployment(s)")

    success_count = 0
    for deployment_id in superseded_ids:
        if stop_deployment(deployment_id, args.dry_run):
            success_count += 1

    if args.dry_run:
        print("Dry run completed. Run without --dry-run to actually stop deployments.")
    else:
        print(f"Deployment cleanup completed. {success_count}/{len(superseded_ids)} deployments stopped successfully.")
        if success_count < len(superseded_ids):
            sys.exit(1)


if __name__ == '__main__':
    main()
