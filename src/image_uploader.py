import os

import paramiko  # type: ignore
from dotenv import load_dotenv


class SSHFileTransfer:
    """A class for uploading and downloading files over SSH."""

    def __init__(
        self,
        username: str,
        hostname: str,
        port: int,
        password: str,
    ) -> None:
        self.username = username
        self.hostname = hostname
        self.port = port
        self.password = password
        self.ssh = None
        self.sftp = None

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

    def upload_file(self, local_file, remote_path):
        try:
            self.sftp.put(local_file, remote_path)
            print('File uploaded successfully!')
        except Exception as e:
            print(f"Error: {e}")

    def download_file(self, remote_file, local_path):
        try:
            self.sftp.get(remote_file, local_path)
            print('File downloaded successfully!')
        except Exception as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    load_dotenv()
    hostname = os.environ.get('HOSTNAME')
    username = os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    port = int(os.environ.get('PORT'))

    ssh_file_transfer = SSHFileTransfer(
        username=username,
        hostname=hostname,
        port=port,
        password=password,
    )
    ssh_file_transfer.connect()
    ssh_file_transfer.upload_file('local_file', 'remote_file')
    ssh_file_transfer.download_file('remote_file', 'local_file')
    ssh_file_transfer.disconnect()
