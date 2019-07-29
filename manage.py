import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path

SRC_FOLDER = "organize"
CURRENT_FOLDER = Path(__file__).resolve().parent


def ask_confirm(text):
    while True:
        answer = input(f"{text} [Y/n]: ").lower()
        if answer in ("j", "y", "ja", "yes"):
            return True
        if answer in ("n", "no", "nein"):
            return False


def set_version(args):
    """
    - reads and validates version number
    - updates __version__.py
    - updates pyproject.toml
    - Searches for 'WIP' in changelog and replaces it with current version and date
    """
    version = args.version

    # read version from input if not given
    if not version:
        version = input("Version number: ")

    # validate and remove 'v' if present
    version = version.lower()
    if not re.match(r"v?\d+\.\d+.*", version):
        return
    if version.startswith("v"):
        version = version[1:]

    # safety check
    if not ask_confirm(f"Creating version v{version}. Continue? [Y/n]"):
        return

    # update library version
    versionfile = CURRENT_FOLDER / SRC_FOLDER / "__version__.py"
    with open(versionfile, "w") as f:
        print(f"Updating {versionfile}")
        f.write(f'__version__ = "{version}"\n')

    # update poetry version
    print("Updating pyproject.toml")
    subprocess.run(["poetry", "version", version], check=True)

    # read changelog
    print("Updating CHANGELOG.md")
    with open(CURRENT_FOLDER / "CHANGELOG.md", "r") as f:
        changelog = f.read()

    # check if WIP section is in changelog
    wip_regex = re.compile(r"## WIP\n(.*?)(?=\n##)", re.MULTILINE | re.DOTALL)
    match = wip_regex.search(changelog)
    if not match:
        print('No "## WIP" section found in changelog')
        return

    # change WIP to version number and date
    changes = match.group(1)
    today = datetime.now().strftime("%Y-%m-%d")
    changelog = wip_regex.sub(f"## v{version} ({today})\n{changes}", changelog, count=1)

    # write changelog
    with open(CURRENT_FOLDER / "CHANGELOG.md", "w") as f:
        f.write(changelog)

    print("Success.")


def publish(args):
    """
    - reads version
    - creates git tag
    - pushes to github
    - publishes on pypi
    """
    from organize.__version__ import __version__ as version

    if not ask_confirm(f"Publishing version {version}. Is this correct?"):
        return

    # create git tag ('vXXX')
    if ask_confirm("Create tag?"):
        subprocess.run(["git", "tag", "-a", f"v{version}", "-m", f"v{version}"])

    # push to github
    if ask_confirm("Push to github?"):
        print("Pushing to github")
        subprocess.run(["git", "push", "--follow-tags"], check=True)

    # upload to pypi
    if ask_confirm("Publish on Pypi?"):
        subprocess.run(["rm", "-rf", "dist"], check=True)
        subprocess.run(["poetry", "build"], check=True)
        subprocess.run(["poetry", "publish"], check=True)

    # TODO: create github release with changelog
    # TODO: trigger readthedocs?
    print("Success.")


def main():
    assert CURRENT_FOLDER == Path.cwd().resolve()

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_version = subparsers.add_parser("version", help="Set the version number")
    parser_version.add_argument(
        "version", type=str, help="The version number", nargs="?", default=None
    )
    parser_version.set_defaults(func=set_version)

    parser_publish = subparsers.add_parser("publish", help="Publish the project")
    parser_publish.set_defaults(func=publish)

    args = parser.parse_args()
    if not vars(args):
        parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()