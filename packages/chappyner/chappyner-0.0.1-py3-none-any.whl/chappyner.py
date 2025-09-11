#!/usr/bin/env python3

import argparse, sys, subprocess
import yaml

def main():
    args = get_arguments()

    print(f"Username: {args.user}")
    print(f"Cluster: {args.cluster}")
    print(f"Service: {args.service}")

def get_arguments():
    parser = argparse.ArgumentParser(description='A description of the program.')

    parser.add_argument('-c', '--cluster', metavar='CLUSTER',
                        dest='cluster', required=True,
                        help='Cluster to be used')

    parser.add_argument('-u', '--user', "--username", metavar='USERNAME',
                        dest='user', required=True,
                        help='Username')

    parser.add_argument('-s', '--service', metavar='SERVICE',
                        dest='service', required=True,
                        help='Service: vnc, jupyter, ttyd')

    args = parser.parse_args()

    return args

def run_local(command):
    """Run a local command and return stdout, stderr, and the exit code."""
    result = subprocess.run(
        command,
        shell=True,           # True if passing a single string; False if passing a list
        capture_output=True,  # capture both stdout and stderr
        text=True             # return strings instead of bytes
    )
    return result.stdout, result.stderr, result.returncode

def run_remote(host, user, command, keyfile=None):
    """
    Run a command on a remote host via SSH using subprocess.

    host: remote host (IP or hostname)
    user: SSH username
    command: command to execute remotely
    keyfile: path to a private key file to use, optional
    """
    ssh_cmd = ["ssh"]
    if keyfile:
        ssh_cmd += ["-i", keyfile]
    ssh_cmd.append(f"{user}@{host}")
    ssh_cmd.append(command)

    result = subprocess.run(
        ssh_cmd,
        capture_output=True,
        text=True
    )
    return result.stdout, result.stderr, result.returncode

if __name__ == "__main__":
    main()
