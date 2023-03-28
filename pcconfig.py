import pynecone as pc

config = pc.Config(
    app_name="endoscreen",
    db_url="sqlite:///pynecone.db",
    env=pc.Env.DEV,
)
