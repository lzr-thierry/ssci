import os
import sys
import argparse
import subprocess
from typing import Set

# Constants for default settings
DEFAULT_OUTPUT_FILE = "full_code.txt"

# Default set of programming and configuration-related file extensions
DEFAULT_PROGRAMMING_EXTENSIONS = {
    '', '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.vb', '.r', '.rb',
    '.go', '.php', '.swift', '.kt', '.rs', '.scala', '.pl', '.lua', '.jl',
    '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss', '.less', '.sass',
    '.sh', '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.sql', '.psql', '.db',
    '.sqlite', '.xml', '.json', '.toml', '.ini', '.yml', '.yaml',
    '.rst', '.Makefile', '.gradle', '.cmake', '.ninja', '.pqm', '.pq'
}

DEFAULT_EXCLUDE_DIRS = {
    'venv', 'node_modules', '__pycache__', '.git', 'dist', 'build', 'temp',
    'tempDir', 'linux64GccDPInt32Opt', 'old_files', 'flask_session'
}

DEFAULT_EXCLUDE_FILES = {
    os.path.basename(__file__),
    'package-lock.json', 'package.json', 'temp.py', '.gitignore',
    'full_code.txt'
}


def parse_arguments():
    """
    Parse command-line arguments for directory scanning and file aggregation.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Aggregate code files into a single output."
    )
    parser.add_argument(
        '-c', '--clipboard', action='store_true',
        help="Copy result to clipboard."
    )
    parser.add_argument(
        '-d', '--directory', default=os.getcwd(),
        help="Root directory to search from."
    )
    parser.add_argument(
        '-o', '--output-file', default=DEFAULT_OUTPUT_FILE,
        help="Output filename."
    )
    parser.add_argument(
        '-i', '--include-files', default="",
        help="Comma-separated list of files to include."
    )
    parser.add_argument(
        '-x', '--extensions', default="",
        help="Comma-separated list of file extensions to include."
    )
    parser.add_argument(
        '-e', '--exclude-dirs', default="",
        help="Comma-separated list of directories to exclude."
    )
    parser.add_argument(
        '-X', '--exclude-extensions', default="",
        help="Comma-separated list of extensions to exclude."
    )
    return parser.parse_args()


def parse_set_arg(arg: str) -> Set[str]:
    """
    Convert a comma-separated string into a set of non-empty trimmed strings.

    Args:
        arg (str): Comma-separated input string.

    Returns:
        Set[str]: Set of trimmed strings.
    """
    return {item.strip() for item in arg.split(',') if item.strip()}


def is_programming_file(name: str, exts: Set[str],
                        excl_exts: Set[str]) -> bool:
    """
    Check if a file has a valid programming-related extension.

    Args:
        name (str): File name.
        exts (Set[str]): Extensions to include.
        excl_exts (Set[str]): Extensions to exclude.

    Returns:
        bool: True if file should be considered, False otherwise.
    """
    _, ext = os.path.splitext(name.lower())
    return ext in exts and ext not in excl_exts


def should_exclude(path: str, excl_dirs: Set[str],
                   excl_files: Set[str]) -> bool:
    """
    Determine whether a file or its parent directories should be excluded.

    Args:
        path (str): Relative file path.
        excl_dirs (Set[str]): Directories to exclude.
        excl_files (Set[str]): File names to exclude.

    Returns:
        bool: True if excluded, False otherwise.
    """
    parts = os.path.normpath(path).split(os.sep)
    return any(p in excl_dirs for p in parts[:-1]) or parts[-1] in excl_files


def should_include_file(path: str, includes: Set[str]) -> bool:
    """
    Determine whether a file should be included based on an include list.

    Args:
        path (str): Full file path.
        includes (Set[str]): Set of relative file paths to include.

    Returns:
        bool: True if file should be included, False otherwise.
    """
    return not includes or os.path.relpath(path) in includes


def generate_tree(start: str, excl_dirs: Set[str],
                  excl_files: Set[str]) -> str:
    """
    Generate a visual directory tree, excluding certain files and directories.

    Args:
        start (str): Root directory.
        excl_dirs (Set[str]): Directories to exclude.
        excl_files (Set[str]): Files to exclude.

    Returns:
        str: Directory tree as a formatted string.
    """
    lines = []
    for root, dirs, files in os.walk(start):
        rel = os.path.relpath(root, start)
        parts = rel.split(os.sep) if rel != '.' else []
        level = len(parts)
        indent = '│   ' * level
        base = os.path.basename(root.rstrip(os.sep))

        if base in excl_dirs:
            dirs.clear()
            continue

        lines.append(f"{indent}├── {base}/")
        for name in files:
            if name not in excl_files:
                lines.append(f"{indent}│   ├── {name}")
    return '\n'.join(lines)


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to system clipboard (macOS only using pbcopy).

    Args:
        text (str): Text to copy.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        subprocess.run(['pbcopy'], input=text.encode(), check=True)
        return True
    except Exception as e:
        print(f"Clipboard error: {e}")
        return False


def aggregate_files(
    start: str,
    output_file: str,
    includes: Set[str],
    exts: Set[str],
    excl_dirs: Set[str],
    excl_exts: Set[str],
    excl_files: Set[str],
    to_clipboard: bool
):
    """
    Aggregate content from code files into a single output.

    Args:
        start (str): Root directory to search.
        output_file (str): Path to the output file.
        includes (Set[str]): Specific files to include.
        exts (Set[str]): Extensions to include.
        excl_dirs (Set[str]): Directories to exclude.
        excl_exts (Set[str]): Extensions to exclude.
        excl_files (Set[str]): File names to exclude.
        to_clipboard (bool): Whether to copy output to clipboard.
    """
    if not os.path.isdir(start):
        print(f"Error: directory '{start}' does not exist.")
        sys.exit(1)

    result = ["Directory Tree:",
              generate_tree(start, excl_dirs, excl_files), ""]

    for root, dirs, files in os.walk(start):
        rel = os.path.relpath(root, start)
        parts = rel.split(os.sep) if rel != '.' else []

        if any(p in excl_dirs for p in parts):
            dirs.clear()
            continue

        for name in files:
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, start)

            if should_exclude(rel_path, excl_dirs, excl_files):
                continue
            if not is_programming_file(name, exts, excl_exts):
                continue
            if not should_include_file(full_path, includes):
                continue

            result.append("\n\n# ======================")
            result.append(f"# File: {rel_path}")
            result.append("# ======================")
            try:
                with open(full_path, encoding='utf-8') as f:
                    result.append(f.read())
            except Exception as e:
                result.append(f"# Error reading {rel_path}: {e}")

    output = '\n'.join(result)

    if to_clipboard:
        if copy_to_clipboard(output):
            print("Copied to clipboard.")
        else:
            sys.exit(1)
    else:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Written to '{output_file}'.")
        except Exception as e:
            print(f"Error writing file: {e}")
            sys.exit(1)


if __name__ == "__main__":
    args = parse_arguments()
    includes = parse_set_arg(args.include_files)
    exts = parse_set_arg(args.extensions) or DEFAULT_PROGRAMMING_EXTENSIONS
    excl_dirs = parse_set_arg(args.exclude_dirs) or DEFAULT_EXCLUDE_DIRS
    excl_exts = parse_set_arg(args.exclude_extensions)

    aggregate_files(
        start=args.directory,
        output_file=args.output_file,
        includes=includes,
        exts=exts,
        excl_dirs=excl_dirs,
        excl_exts=excl_exts,
        excl_files=DEFAULT_EXCLUDE_FILES,
        to_clipboard=args.clipboard
    )
