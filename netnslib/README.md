This is a Python wrapper for the `setns()` system call.

## Examples

Show interface configuration inside a named network namespace:

    import netns
    import subprocess

    with netns.NetNS(nsname='myns'):
        subprocess.call(['ip', 'a'])

Inspect the interface configuration inside a docker container
(assuming that you have retrieved the container pid via `docker
inspect` output or by using the Docker API):

    with netns.NetNS(nspid=29435):
        subprocess.call(['ip', 'a'])

Create a socket inside a network namespace:

    sock = netns.socket(netns.get_ns_path(nsname='myns'))
