from os import getcwd
from pathlib import Path

from bcrypt import gensalt, hashpw

from .cli_helper import input_single, input_password
from .config import Config


def generate_htpasswd(
    username: str,
    password: str,
    htpasswd_file: Path,
    encoding: str = Config.encoding,
) -> None:
    """Create ore extend .htpasswd"""
    hashed = hashpw(password.encode(encoding), gensalt())
    entry = f"{username}:{hashed.decode()}\n"

    mode = "a" if htpasswd_file.exists() else "w"

    with htpasswd_file.open(mode, encoding=encoding) as f:
        f.write(entry)

    print(f"✅ User '{username}' add to {htpasswd_file.absolute().as_posix()}")


def username_menu() -> str:
    return input_single("Username:", input_type=str)


def password_menu() -> str:
    return input_password()


def menu() -> None:
    username = username_menu()
    password = password_menu()

    htpasswd = Path(getcwd()) / ".htpasswd"

    generate_htpasswd(username, password, htpasswd)


def run() -> None:
    try:
        menu()
    except KeyboardInterrupt:
        print("Cancelled")


if __name__ == "__main__":
    run()
