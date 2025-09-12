import asyncio
import getpass
import os
import socket

import edwh.tasks
from edwh import task
from invoke import Context, context
from plumbum import BG, local


def get_remote_available_ports(c: Context):
    """
    Retrieves the list of available ports on the remote server.

    Args:
        c: The connection object used to communicate with the remote server.

    Returns:
        list: A list of available port numbers on the remote server.
    """

    port_cmd = c.run("nc -z -v 127.0.0.1 2220-2300 2>&1 | grep refused | cut -d ' ' -f 6", hide=True)
    # return available_port
    return port_cmd.stdout.split("\n")


def get_available_port(c: Context):
    """
    Retrieves an available port that is both locally and remotely accessible.

    Args:
        c: The connection object used to communicate with the remote server.

    Returns:
        int: An available port number that is both locally and remotely accessible.
    """
    # get remote available ports
    remote_ports = get_remote_available_ports(c)

    # check if a local port is in a remote port
    for local_port in get_local_available_port():
        if local_port in remote_ports:
            return local_port


# check if there are any available ports
def get_local_available_port(start_port: int = 2222):
    """
    Retrieves a list of available ports on the local machine.

    Args:
        start_port (optional): The starting port number to search for available ports.
            Defaults to 2222.

    Returns:
        list: A list of available port numbers on the local machine.
    """
    available_ports = []

    # check all ports between start_port and 60000
    for port in range(start_port, 2300):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.connect(("127.0.0.1", port))
            continue
        except Exception:
            available_ports.append(str(port))
        finally:
            s.close()

    return available_ports


@task(hookable=False)
def setup(c: Context):
    """
    Installs the necessary packages for SSHFS.
    """
    if edwh.tasks.require_sudo(c):
        c.sudo("apt update")
        c.sudo("apt install -y openssh-client openssh-server sshfs")
        c.sudo("systemctl enable ssh")
        c.sudo("ufw allow ssh")


@task()
def ensure_sshfs(c: Context):
    """
    Ensures that SSHFS is installed on the local machine.
    """
    if not c.run("which sshfs", hide=True, warn=True).ok:
        setup(c)


@task(help={"folder": "The directory path to be unmounted."}, pre=[ensure_sshfs])
def unmount_dir(c, folder):
    """
    Unmounts a directory on the server.

    Returns:
        None
    """

    umount_server_dir = f"umount {folder}"
    print(f"running {umount_server_dir}")
    if not c.run(umount_server_dir, warn=True).ok:
        print("cannot unmount because following processes are still running and using the mount")
        c.run(f"lsof -n {folder} 2>/dev/null")
        pids = c.run("lsof -t -n /home/ubuntu/testing 2>/dev/null", hide=True).stdout.strip().split("\n")
        print(f"Terminate with: kill {' '.join(pids)}; sleep 2; umount {folder}")
    else:
        print("suFccessfully exited :)")


@task(
    help={
        "workstation-dir": "The directory path on the local machine to mount the server directory.",
        "server-dir": "The directory path on the remote server to be mounted.",
        "queue": "An optional queue object used for synchronization. Defaults to None, optional",
    },
    pre=[ensure_sshfs],
)
def remote_mount(
    c,
    workstation_dir,
    server_dir,
    queue=None,
):
    """
    The remote_mount function is an asynchronous Python task that allows you to mount a remote directory
    on your local machine using SSHFS (SSH Filesystem). It establishes a secure connection to a remote server,
    forwards a port, and mounts the remote directory on the local machine.

    Returns:
        None
    """
    if not hasattr(c, "host"):
        print("please provide a host using -H")
        exit(255)

    # get an available port that is usable on local and remote so we can setup a connection with the ports
    port = get_available_port(c)
    ssh_cmd = local["ssh"]["-A", f"-R {port}:127.0.0.1:22", f"{c.user}@{c.host}"]
    sshfs_cmd = ssh_cmd[
        "sshfs",
        "-f",
        f"-p {port}",
        "-o allow_root,default_permissions",
        "-o StrictHostKeyChecking=no,reconnect,ServerAliveInterval=3,ServerAliveCountMax=3,"
        f"uid={os.getuid()},gid={os.getgid()}",
        f"{getpass.getuser()}@127.0.0.1:{workstation_dir}",
        f"{server_dir}",
    ]

    if not queue:
        print(f"starting sshfs with(started when nothing happens): {str(sshfs_cmd)}")
    try:
        sshfs_cmd()
    except KeyboardInterrupt:
        unmount_dir(c, server_dir)


@task(
    help={
        "workstation-dir": "The directory path on the local machine to be mounted.",
        "server-dir": "The directory path on the remote server to mount the workstation directory.",
        "queue": "An optional queue object used for synchronization. Defaults to None, optional",
    },
    pre=[ensure_sshfs],
)
def local_mount(c, workstation_dir, server_dir, queue=None):
    """
    The local_mount function is a Python task that enables the mounting of a remote directory on a local workstation
    using SSHFS (SSH Filesystem). It establishes a secure connection to a remote server and mounts a specified
    directory from the server onto a local directory on the workstation.

    Returns:
        None
    """
    # os.popen(f"lsof -n {workstation_dir} 2>/dev/null")
    if not hasattr(c, "host"):
        print("please provide a host using -H")
        exit(255)

    # TODO: remove mount on exit
    sshfs_cmd = local["sshfs"][
        "-f",
        "-o",
        "allow_root,default_permissions,umask=000,StrictHostKeyChecking=no,reconnect,"
        f"uid={os.getuid()},gid={os.getgid()}",
        f"{c.user}@{c.host}:{server_dir}",
        workstation_dir,
    ]

    if not queue:
        print("running sshfs...")

    sshfs_cmd()

    local_connection = context.Context()
    local_connection.run(f"umount {workstation_dir}", hide=True)


# ----------------------------------#
# |             async              |#
# ----------------------------------#


async def async_local_mount(c, workstation_dir, server_dir, event=None):
    """
    async version of local_mount
    """
    if not hasattr(c, "host"):
        print("please provide a host using -H")
        exit(255)

    sshfs_cmd = local["sshfs"][
        "-f",
        "-o",
        "allow_root,default_permissions,umask=000,StrictHostKeyChecking=no,reconnect,"
        f"uid={os.getuid()},gid={os.getgid()}",
        f"{c.user}@{c.host}:{server_dir}",
        workstation_dir,
    ]

    if not event:
        print("running sshfs...")

    process = sshfs_cmd & BG
    await event.wait()

    process.proc.terminate()

    local_connection = context.Context()
    local_connection.run(f"umount {workstation_dir}", warn=True, hide=True)

    # await anyio.sleep(1)
    await asyncio.sleep(1)


async def async_remote_mount(c, workstation_dir, server_dir, event=None):
    """
    async version of remote_mount
    """
    if not hasattr(c, "host"):
        print("please provide a host using -H")
        exit(255)

    # get an available port that is usable on local and remote so we can setup a connection with the ports
    port = get_available_port(c)
    ssh_cmd = local["ssh"]["-A", f"-R {port}:127.0.0.1:22", f"{c.user}@{c.host}"]
    sshfs_cmd = ssh_cmd[
        "sshfs",
        "-f",
        f"-p {port}",
        "-o allow_root,default_permissions",
        "-o StrictHostKeyChecking=no,reconnect,ServerAliveInterval=3,ServerAliveCountMax=3,"
        f"uid={os.getuid()},gid={os.getgid()}",
        f"{getpass.getuser()}@127.0.0.1:{workstation_dir}",
        f"{server_dir}",
    ]

    if not event:
        print(f"starting sshfs with(started when nothing happens): {str(sshfs_cmd)}")
    try:
        process = sshfs_cmd & BG
        await event.wait()
        process.proc.terminate()
        # await anyio.sleep(1)
        await asyncio.sleep(1)
        c.run(f"umount {server_dir}", warn=True, hide=True)
    except KeyboardInterrupt:
        unmount_dir(c, server_dir)
