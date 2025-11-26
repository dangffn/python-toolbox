import argparse
from typing import Literal
import json
from rich.table import Table, Column

from toolbox.subcommands.loader import register
from toolbox.logger import console
from toolbox.net.ipv4 import Config
from toolbox.net.ssh_browser import ssh_browser


def show_ip(ip_address: str, output: Literal["print", "json"]) -> None:
    data = Config(ip_address).to_json()
    if output == "print":
        table = Table(
            Column("Key", style="#444444"),
            Column("Value", style="cyan"),
            border_style="#444444"
        )
        for key, val in data.items():
            key = " ".join(key.capitalize().split("_"))
            if isinstance(val, int):
                table.add_row(key, f"{val:,}")
            else:
                table.add_row(key, str(val))
        console.print(table)
    else:
        print(json.dumps(data, indent=4))
        

@register("net", description="Network related utilities")
def setup_net(parser: argparse.ArgumentParser) -> None:
    parser.set_defaults(func=parser.print_help)


@register("net", "ipv4", description="IPv4 related network utilities")
def setup_net_ipv4(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("ip_address", help="IPv4 address in CIDR notation ie. 0.0.0.0/0")
    parser.add_argument("--output", default="print", choices=["print", "json"], help="Output format")
    parser.set_defaults(func=show_ip)
    
    
@register("net", "ssh-browser", description="Browse files on a remote system over SSH in your CLI")
def setup_net_ssh_browser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("connection_str", help="SSH resource to browse (ie. <user>@<hostname>:<path>). If <user> is omitted, the current account will be used. If <path> is omitted, will default to root")
    parser.add_argument("--port", "-p", default=22, type=int, help="The SSH port to use, default: 22.")
    parser.set_defaults(func=ssh_browser)