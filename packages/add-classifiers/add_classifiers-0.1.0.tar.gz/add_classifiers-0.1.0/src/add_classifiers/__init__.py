from argparse import ArgumentParser
from pathlib import Path

from packaging.requirements import Requirement
from packaging.version import parse
from pzp import pzp
from tomlkit import array, dump, load
from trove_classifiers import sorted_classifiers


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--pyproject",
        nargs="?",
        type=Path,
        default="pyproject.toml",
        help="Path to pyproject %(default)s",
    )
    subparsers = parser.add_subparsers(dest="command")
    # Used to add subcommands
    # currently not using anything except global params
    _ = subparsers.add_parser("add")
    _ = subparsers.add_parser("suggest")

    args = parser.parse_args()

    match args.command:
        case "add":
            return add(args, sorted_classifiers)
        case "suggest":
            return suggest(args)
        case None:
            parser.print_help()


def add(args, classifiers_list):
    choice = pzp(classifiers_list)
    if choice is None:
        print("exited")
        return 1
    if args.pyproject.exists():
        with args.pyproject.open("rb") as fp:
            pyproject = load(fp)
            try:
                classifiers = set(pyproject["project"]["classifiers"])
            except KeyError:
                classifiers = set()

            classifiers.add(choice)

            tbl = array()
            tbl.multiline(True)
            tbl.extend(sorted(classifiers))
            pyproject["project"]["classifiers"] = tbl
        with args.pyproject.open("w") as fp:
            dump(pyproject, fp)


def suggest(args):
    # Sort and filter the classifiers that we can check for
    python_classifiers = {}
    django_classifiers = {}

    for classifier in sorted_classifiers:
        match classifier.split(" :: "):
            case ("Programming Language", "Python", version) | (
                "Programming Language",
                "Python",
                version,
                "Only",
            ):
                try:
                    python_classifiers[parse(version.strip())] = classifier
                except Exception:
                    print("Python", version)
            case "Framework", "Django", version:
                try:
                    django_classifiers[parse(version.strip())] = classifier
                except Exception:
                    print("Unknown django", version)

    # Start checking our pyproject file for what classifiers we think we can add
    suggested_list = set()
    with args.pyproject.open("rb") as fp:
        pyproject = load(fp)
        if "requires-python" in pyproject["project"]:
            requires_python = pyproject["project"]["requires-python"]

            if requires_python.startswith(">="):
                python_version = parse(requires_python[2:])
                for version in python_classifiers:
                    if version >= python_version:
                        suggested_list.add(python_classifiers[version])
            else:
                python_version = parse(requires_python)
                if python_version in python_classifiers:
                    suggested_list.add(python_classifiers[python_version])

        # Any project specific dependencies that we want to support
        for dep in pyproject["project"].get("dependencies", []):
            dep = Requirement(dep)
            match dep.name.lower():
                case "django":
                    for version in django_classifiers:
                        if dep.specifier.contains(version):
                            suggested_list.add(django_classifiers[version])

    try:
        classifiers = set(pyproject["project"]["classifiers"])
    except KeyError:
        classifiers = set()

    classifiers.update(suggested_list)

    tbl = array()
    tbl.multiline(True)
    tbl.extend(sorted(classifiers))
    pyproject["project"]["classifiers"] = tbl
    with args.pyproject.open("w") as fp:
        dump(pyproject, fp)


if __name__ == "__main__":
    main()
