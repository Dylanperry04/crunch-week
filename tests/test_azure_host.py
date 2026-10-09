import os
import subprocess
import sys


def test_azure_host_is_allowed_without_allowing_other_domains():
    # Import the app in its own process so middleware reads startup configuration.
    env = dict(os.environ)
    env.update(
        {
            "PYTHON_DOTENV_DISABLED": "1",
            "ALLOWED_HOSTS": "localhost, 127.0.0.1 ,custom.example",
            "WEBSITE_HOSTNAME": "example.swedencentral-01.azurewebsites.net",
        }
    )
    code = """
from fastapi.testclient import TestClient
from crunch_week.api import app
with TestClient(app) as client:
    for host in ('localhost', '127.0.0.1', 'custom.example', 'example.swedencentral-01.azurewebsites.net'):
        assert client.get('/api/health', headers={'host': host}).status_code == 200
    assert client.get('/api/health', headers={'host': 'untrusted.example'}).status_code == 400
print('Host validation passed')
"""
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "Host validation passed" in result.stdout
