import os
import re
from pathlib import Path
from shutil import move

import click

# Category regexes
CATEGORY_PATTERNS = {
    'news': [r'nytimes\.com', r'bbc\.co\.uk', r'444\.hu', r'telex\.hu'],
    'music': [r'spotify\.com', r'soundcloud\.com'],
    'learn': [r'khanacademy\.org', r'coursera\.org', r'edx\.org'],
}

def categorize_line(line):
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return category
    return None

@click.command()
@click.option('--input-dir', '-i', required=True, type=click.Path(exists=True, file_okay=False), help='Directory with input .txt files.')
@click.option('--output-dir', '-o', required=True, type=click.Path(file_okay=False), help='Directory to write category files to.')
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm all moves (non-interactive).')
@click.option('--remove-moved-lines', is_flag=True, help='Remove lines from source files based on lines moved into category files.')
def categorize_websites(input_dir, output_dir, yes, remove_moved_lines):
    """Categorize websites into category files. Optionally remove moved lines from original files."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    all_moves = []  # To track what was moved: (file, line_num, line, category)

    # Step 1: Categorize lines without touching original files
    for file in input_path.glob("*.txt"):
        with file.open('r', encoding='utf-8') as f:
            lines = f.readlines()

        for idx, line in enumerate(lines, 1):
            category = categorize_line(line)
            if category:
                target_file = output_path / f"{category}.txt"
                print(f"{file.name}:{idx} {line.strip()} --> {target_file.name}")
                if yes or click.confirm("Confirm move?"):
                    with target_file.open('a', encoding='utf-8') as tf:
                        tf.write(line)
                    all_moves.append((file, idx, line, category))

    # Step 2: Optionally remove moved lines from original files
    if remove_moved_lines and all_moves:
        print("\n--- Removing moved lines from source files ---")
        # Group by file
        file_map = {}
        for file, idx, line, _ in all_moves:
            file_map.setdefault(file, []).append((idx, line))

        for file, removals in file_map.items():
            with file.open('r', encoding='utf-8') as f:
                lines = f.readlines()

            removal_indexes = {idx - 1 for idx, _ in removals}  # line numbers to 0-based indexes
            kept_lines = []
            for i, line in enumerate(lines):
                if i in removal_indexes:
                    print(f"{file.name}:{i+1} {line.strip()} --> REMOVED")
                    if not (yes or click.confirm("Confirm removal?")):
                        kept_lines.append(line)
                else:
                    kept_lines.append(line)

            with file.open('w', encoding='utf-8') as f:
                f.writelines(kept_lines)

if __name__ == '__main__':
    categorize_websites()
