import pynecone as pc

config = pc.Config(
    app_name="endoscreen",
    frontend_packages = ['react-camera-pro','styled-components'],
    db_url="sqlite:///pynecone.db",
    env=pc.Env.DEV,
)
