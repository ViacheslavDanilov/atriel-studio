import logging
import os
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

    def connect(self) -> None:
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
            logging.info(f'Error: {e}')

    def disconnect(self) -> None:
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
    ) -> None:
        try:
            self.sftp.put(local_path, remote_path)
        except Exception as e:
            logging.info(f'Error: {e}')
            logging.info(f'Local path: {local_path}')
            logging.info(f'Remote path: {remote_path}')

    def download_file(
        self,
        remote_path: str,
        local_path: str,
    ) -> None:
        try:
            self.sftp.get(remote_path, local_path)
        except Exception as e:
            logging.info(f'Error: {e}')

    def create_remote_dir(self, remote_dir: str) -> None:
        try:
            logging.debug(f'Create directory: {remote_dir}')
            self.ssh.exec_command(f'mkdir -p {remote_dir}')
        except Exception as e:
            logging.info(f'Error: {e}')

    def remove_remote_dir(self, remote_dir: str) -> None:
        try:
            logging.debug(f'Remove directory: {remote_dir}')
            self.ssh.exec_command(f'rm -rf {remote_dir} || true')
        except Exception as e:
            logging.info(f'Error: {e}')


if __name__ == '__main__':
    load_dotenv()
    hostname = os.environ.get('SERVER_NAME')
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
    ssh_file_transfer.upload_file(local_path=local_path, remote_path=remote_path)
    ssh_file_transfer.disconnect()

    # Download image
    local_path = 'data/test-hero-downloaded.jpg'
    ssh_file_transfer.connect()
    ssh_file_transfer.download_file(remote_path=remote_path, local_path=local_path)
    # ssh_file_transfer.remove_remote_dir(remote_dir=remote_dir)
    ssh_file_transfer.disconnect()
