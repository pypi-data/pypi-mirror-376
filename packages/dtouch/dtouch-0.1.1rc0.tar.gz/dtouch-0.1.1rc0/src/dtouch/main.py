import argparse
from pathlib import Path

def create_directory_and_file(file_path):
    """
    Creates the parent directory for a file and then creates the file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    print(f"Directory '{path.parent}' created.")
    print(f"File '{path}' created.")

def main():
    """
    Parses command-line arguments and calls the main function.
    """
    parser = argparse.ArgumentParser(
        prog="dtouch",
        description="Create a directory and a file in a single command."
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="The path to the file to create, including its directory."
    )
    args = parser.parse_args()
    create_directory_and_file(args.file_path)

if __name__ == "__main__":
    main()
