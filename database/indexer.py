import json
import os
from pathlib import Path

from database.database import add_folder, clear_folders


CONFIG_PATH = Path("config") / "config.json"


def load_search_locations():

    try:

        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config = json.load(file)

        configured_locations = config.get(
            "search_locations",
            []
        )

        locations = []

        for location in configured_locations:

            expanded_location = os.path.expandvars(
                location
            )

            path = Path(expanded_location)

            if path.exists():
                locations.append(path)

        return locations

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        return []


def build_folder_index():

    print("Building folder index...")

    clear_folders()

    search_locations = load_search_locations()

    folder_count = 0

    for base_path in search_locations:

        print(f"Scanning: {base_path}")

        # Store the search location itself
        add_folder(
            base_path.name,
            base_path
        )

        folder_count += 1

        try:

            for root, directories, files in os.walk(base_path):

                for directory in directories:

                    folder_path = Path(root) / directory

                    add_folder(
                        directory,
                        folder_path
                    )

                    folder_count += 1

        except (
            PermissionError,
            OSError
        ):

            continue

    print(
        f"Folder indexing complete. "
        f"{folder_count} folders indexed."
    )


if __name__ == "__main__":

    from database.database import create_tables

    create_tables()

    build_folder_index()