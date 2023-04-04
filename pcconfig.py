import socket

import pynecone as pc
if 'MacBook' in socket.gethostname():
    config = pc.Config(
        app_name="endoscreen",
        frontend_packages = [],
        db_url="sqlite:///pynecone.db",
        env=pc.Env.DEV,
    )
else:
    config = pc.Config(
        app_name="endoscreen",
        # api_url="0.0.0.0",
        bun_path="/app/.bun/bin/bun",
        frontend_packages = [],
        db_url="sqlite:///pynecone.db",
        env=pc.Env.PROD,
        port=8080,
    )