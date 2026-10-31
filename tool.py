"""Discover common KubeVirt CPU models and feature labels across real schedulable Ready nodes."""
import argparse
from decimal import Decimal
import json
import sys
import subprocess
from datetime import datetime, timezone
from oc_client import Client, VM, VMI, MIG, SNAP, quantity, age_hours, condition, require_name, stopped, escape, migration


def execute(client,args):
    nodes = [n for n in client.items('nodes') if not n.get('spec',{}).get('unschedulable') and condition(n,'Ready').get('status') == 'True' and n['metadata'].get('labels',{}).get('kubevirt.io/schedulable') == 'true']
    sets = [{key for key,value in node['metadata'].get('labels',{}).items() if value == 'true' and key.startswith(('cpu-feature.node.kubevirt.io/','cpu-model.node.kubevirt.io/'))} for node in nodes]
    return {'nodes':[node['metadata']['name'] for node in nodes],'common_labels':sorted(set.intersection(*sets)) if sets else [],'node_count':len(nodes)}


def main():
    parser = argparse.ArgumentParser(description='Discover common KubeVirt CPU models and feature labels across real schedulable Ready nodes.')
    parser.add_argument('--context',required=True,help='Explicit existing oc kubeconfig context')
    parser.add_argument('--namespace',required=True,help='Namespace for workload operations')
    parser.add_argument('--name',help='Exact workload/resource name where required')
    parser.add_argument('--apply',action='store_true',help='Execute the requested change; default is preview')

    args = parser.parse_args()
    try:
        result = execute(Client(args.context,args.namespace),args)
        print(json.dumps({'context':args.context,'namespace':args.namespace,'collected_at':datetime.now(timezone.utc).isoformat(),'result':result},indent=2))
    except (RuntimeError,ValueError,KeyError,OSError,TimeoutError,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__': raise SystemExit(main())
