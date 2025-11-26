from rich.text import Text
from paramiko.ssh_exception import SSHException, AuthenticationException
import getpass
import os
import stat
from pathlib import Path
from textual.widgets import DirectoryTree, Label
from textual.widgets._directory_tree import DirEntry
from textual.app import App, ComposeResult
import paramiko

from toolbox.logger import console_err


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
        self.ssh.connect(hostname, username=username, allow_agent=True, port=port)
        self.sftp = self.ssh.open_sftp()
        super().__init__(path)

    def on_unmount(self) -> None:
        self.sftp.close()
        self.ssh.close()

    def _get_directory_entries(self, path: Path) -> list[DirEntry]:
        entries: list[DirEntry] = []
        for attr in self.sftp.listdir_attr(str(path)):
            attr.filename
            entries.append(
                DirEntry(
                    path=self.PATH(attr.filename),
                    is_dir=stat.S_ISDIR(attr.st_mode) if attr.st_mode else False,
                )
            )
        return entries


class FileBrowserApp(App):
    path: str
    hostname: str
    username: str
    
    def __init__(self, *args, connection_str: str, port: int=22, **kwargs):
        super().__init__(*args, **kwargs)
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
        except SSHException as e:
            err = f"Failed to connect to {self.conn_str} ({e})"
        except AuthenticationException as e:
            err = f"Failed to authenticate with server {self.conn_str} ({e})"
            
        if err:
            console_err.log(err)
            yield Label(Text(err, style="red"))
        
        
def ssh_browser(connection_str: str, port: int=22) :
    app = FileBrowserApp(connection_str=connection_str, port=port)
    app.run()


if __name__ == "__main__":
    ssh_browser("localhost", port=22)
