import os
import sys
from pathlib import Path

from app.seed import initialize_database


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL must be set before initializing the database.", file=sys.stderr)
        return 1

    seed_file = Path(__file__).resolve().parent.parent / "data" / "projects.json"
    initialize_database(database_url, seed_file)
    print(f"Initialized projects database from {seed_file}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
