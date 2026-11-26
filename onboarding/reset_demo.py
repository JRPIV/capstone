"""Clear the local demonstration case file.

Does not read, print, or change `.env` or any key.
"""

from onboarding.store import DEFAULT_DB_PATH


def main() -> None:
    removed = False
    for suffix in ("", "-wal", "-shm"):
        path = DEFAULT_DB_PATH.parent / f"{DEFAULT_DB_PATH.name}{suffix}"
        if path.is_file():
            path.unlink()
            removed = True
    if removed:
        print("Demo case store cleared. Restart the server before the next demonstration.")
    else:
        print("Demo case store was already empty.")


if __name__ == "__main__":
    main()
