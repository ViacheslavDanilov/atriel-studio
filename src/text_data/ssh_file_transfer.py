import os
import webbrowser
from pathlib import Path

import paramiko
from dotenv import load_dotenv


class SSHFileTransfer:
    """A class for uploading and downloading files over SSH."""

    def __init__(
        self,
        username: str,
        hostname: str,
        port: int,
        password: str,
        url: str,
    ) -> None:
        self.username = username
        self.hostname = hostname
        self.port = port
        self.password = password
        self.url = url

    def connect(self):
        # Create SSH client
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect to the SSH server
            self.ssh.connect(
                self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
            )
            self.sftp = self.ssh.open_sftp()
        except Exception as e:
            print(f"Error: {e}")

    def disconnect(self):
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
    ) -> str:
        try:
            self.sftp.put(local_path, remote_path)
            print('File uploaded successfully!')
            file_url = self._get_file_url(remote_path)
        except Exception as e:
            print(f"Error: {e}")
            file_url = ''

        return file_url

    def download_file(
        self,
        remote_path: str,
        local_path: str,
    ):
        try:
            self.sftp.get(remote_path, local_path)
            print('File downloaded successfully!')
        except Exception as e:
            print(f"Error: {e}")

    def create_remote_dir(self, remote_dir: str) -> None:
        try:
            self.ssh.exec_command(f"mkdir -p {remote_dir}")
            print(f"Remote directory '{remote_dir}' created successfully!")
        except Exception as e:
            print(f"Error: {e}")

    def remove_remote_dir(self, remote_dir: str) -> None:
        try:
            self.ssh.exec_command(f"rm -rf {remote_dir}")
            print(f"Remote directory '{remote_dir}' and its contents removed successfully!")
        except Exception as e:
            print(f"Error: {e}")

    def _get_file_url(self, remote_path: str) -> str:
        file_path = Path(remote_path)
        truncated_path = Path(*file_path.parts[4:])
        file_url = os.path.join(self.url, truncated_path)
        return file_url


if __name__ == '__main__':
    load_dotenv()
    hostname = os.environ.get('HOSTNAME')
    username = os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    port = int(os.environ.get('PORT'))
    remote_root_dir = os.environ.get('REMOTE_ROOT_DIR')
    url = os.environ.get('URL')

    ssh_file_transfer = SSHFileTransfer(
        username=username,
        hostname=hostname,
        port=port,
        password=password,
        url=url,
    )

    # Upload image
    local_path = 'data/test-img.jpg'
    remote_dir = os.path.join(remote_root_dir, 'test-dir')
    remote_path = os.path.join(remote_dir, Path(local_path).name)
    ssh_file_transfer.connect()
    ssh_file_transfer.create_remote_dir(remote_dir)
    file_url = ssh_file_transfer.upload_file(local_path=local_path, remote_path=remote_path)
    webbrowser.open(file_url, new=2)
    ssh_file_transfer.disconnect()

    # Download image
    local_path = 'data/test-hero-downloaded.jpg'
    ssh_file_transfer.connect()
    ssh_file_transfer.download_file(remote_path=remote_path, local_path=local_path)
    # ssh_file_transfer.remove_remote_dir(remote_dir=remote_dir)
    ssh_file_transfer.disconnect()
