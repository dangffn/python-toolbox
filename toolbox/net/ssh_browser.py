import getpass
import os
from pathlib import Path
from typing import Type

import paramiko
from paramiko.ssh_exception import AuthenticationException, SSHException
from rich.text import Text
from textual._path import CSSPathType
from textual.app import App, ComposeResult
from textual.driver import Driver
from textual.widgets import DirectoryTree, Label
from textual.widgets._directory_tree import DirEntry

from toolbox.logger import console_err
from toolbox.subcommands.loader import cli


def use_identity_agent(hostname: str) -> None:
    """Point paramiko at the `IdentityAgent` from ~/.ssh/config (e.g. 1Password).

    Paramiko ignores `IdentityAgent` and only reads `SSH_AUTH_SOCK`, so set that.
    """
    config_path = Path("~/.ssh/config").expanduser()
    if not config_path.is_file():
        return

    agent = paramiko.SSHConfig.from_path(str(config_path)).lookup(hostname).get("identityagent")
    if agent and agent not in ("none", "SSH_AUTH_SOCK"):
        os.environ["SSH_AUTH_SOCK"] = os.path.expanduser(agent)


class SshFileBrowser(DirectoryTree):
    def __init__(
        self,
        path: str | Path,
        *,
        hostname: str,
        username: str,
        port: int,
    ) -> None:
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        use_identity_agent(hostname)
        self.ssh.connect(hostname, username=username, allow_agent=True, port=port)
        self.sftp = self.ssh.open_sftp()
        super().__init__(path)

    def on_unmount(self) -> None:
        self.sftp.close()
        self.ssh.close()

    def _get_directory_entries(self, path: Path) -> list[DirEntry]:
        entries: list[DirEntry] = []
        for attr in self.sftp.listdir_attr(str(path)):
            entries.append(
                DirEntry(
                    path=self.PATH(attr.filename),
                )
            )
        return entries


class FileBrowserApp(App[None]):
    path: str
    hostname: str
    username: str

    def __init__(
        self,
        connection_str: str,
        port: int = 22,
        driver_class: Type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
        ansi_color: bool = False,
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.port = port

        # Determine the connection string + path.
        connection_str, self.path = connection_str.split(":", maxsplit=1) if "/" in connection_str else (connection_str, os.sep)
        # Determine the username + hostname.
        self.username, self.hostname = connection_str.split("@") if "@" in connection_str else (getpass.getuser(), connection_str)
        self.conn_str = f"{self.username}@{self.hostname}"

    def compose(self) -> ComposeResult:
        err = None
        try:
            yield SshFileBrowser(
                self.path,
                hostname=self.hostname,
                username=self.username,
                port=self.port,
            )
        except AuthenticationException as e:
            err = f"Failed to authenticate with server {self.conn_str} ({e})"
        except SSHException as e:
            err = f"Failed to connect to {self.conn_str} ({e})"

        if err:
            console_err.log(err)
            yield Label(Text(err, style="red"))


@cli.register("net", "ssh-browser", positional="connection_str")
def ssh_browser(connection_str: str, port: int=22) :
    """Display a TUI file browser over an SSH connection.

    Args:
        connection_str (str): username@hostname ssh connection string
        port (int, optional): optional port number to use, default: 22
    """
    app = FileBrowserApp(connection_str=connection_str, port=port)
    app.run()


if __name__ == "__main__":
    ssh_browser("localhost", port=22)
