"""Connection settings for data tools; importing this never connects to MySQL."""
import os


def database_config():
    config = {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "steamscope"),
        "connection_timeout": 5,
    }
    if os.getenv("DB_SOCKET"):
        config["unix_socket"] = os.environ["DB_SOCKET"]
    return config
