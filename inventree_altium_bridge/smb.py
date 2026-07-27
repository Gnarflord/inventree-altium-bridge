"""Thin SMB helper (used to write the offer feed out and read the pick-and-place file in).

Uses smbprotocol's high-level `smbclient` API so no volume mount is required — the plugin
connects to the share over the network with credentials from plugin settings.
"""


def _session(host, username, password, domain=""):
    import smbclient
    smbclient.register_session(host, username=username, password=password)
    return smbclient


def unc(host, share, path):
    path = (path or "").lstrip("/\\")
    return rf"\\{host}\{share}\{path}".replace("/", "\\")


def write_bytes(host, share, path, data, username, password, domain=""):
    smbclient = _session(host, username, password, domain)
    target = unc(host, share, path)
    tmp = target + ".tmp"
    with smbclient.open_file(tmp, mode="wb") as fh:      # atomic: write tmp then replace
        fh.write(data)
    try:
        smbclient.replace(tmp, target)
    except Exception:
        smbclient.rename(tmp, target)
    return target


def read_bytes(host, share, path, username, password, domain=""):
    smbclient = _session(host, username, password, domain)
    with smbclient.open_file(unc(host, share, path), mode="rb") as fh:
        return fh.read()
