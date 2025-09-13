import yubikey_manager_lib
import subprocess
import tomllib
import os.path
import urllib.parse
import re
import sys


def main():
    with open(os.path.expanduser("~/.config/yubikey-paste/config.toml"), "rb") as f:
        config = tomllib.load(f)
    pasted = subprocess.check_output(["wl-paste", "--primary"], encoding="utf8")[:-1]
    key = None
    for fn in (
        lambda pasted: pasted,
        lambda pasted: urllib.parse.urlparse(pasted).netloc,
        lambda pasted: re.sub("/.*", "", pasted),
    ):
        needle = fn(pasted)

        if needle in config["mappings"]:
            key = config["mappings"][needle]
            break

        sld_tld = ".".join(needle.split(".")[-2:])
        if sld_tld in config["mappings"]:
            key = config["mappings"][sld_tld]
            break
    if key is None:
        print(f"Cannot find {pasted} in ~/.config/yubikey-paste/config.toml")
        sys.exit(1)
    ykman = yubikey_manager_lib.YKMan()
    value = ykman.run("oath", "accounts", "code", "-s", key)["stdout"][0]
    subprocess.check_call(
        [
            "sudo",
            "/usr/bin/injectinput",
            value + "\\r"
        ]
    )
