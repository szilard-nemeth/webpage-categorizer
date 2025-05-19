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
def process_files(input_dir, output_dir, yes):
    """Categorize websites from .txt files into groups like news/music/learn based on regexes."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for file in input_path.glob("*.txt"):
        with file.open('r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        for idx, line in enumerate(lines, 1):
            category = categorize_line(line)
            if category:
                target_file = output_path / f"{category}.txt"
                print(f"{file.name}:{idx} {line.strip()} --> {target_file.name}")
                if yes or click.confirm("Confirm move?"):
                    with target_file.open('a', encoding='utf-8') as tf:
                        tf.write(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # Rewrite file without moved lines
        with file.open('w', encoding='utf-8') as f:
            f.writelines(new_lines)

if __name__ == '__main__':
    process_files()
