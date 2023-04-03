import pynecone as pc

config = pc.Config(
    app_name="endoscreen",
    api_url="0.0.0.0:8080"
    frontend_packages = [],
    db_url="sqlite:///pynecone.db",
    env=pc.Env.DEV,
)
