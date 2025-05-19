import os
import re
from pathlib import Path
from shutil import move

# Category regexes
CATEGORY_PATTERNS = {
    'news': [r'news', r'nytimes\.com', r'bbc\.co\.uk'],
    'music': [r'spotify\.com', r'soundcloud\.com'],
    'learn': [r'khanacademy\.org', r'coursera\.org', r'edx\.org'],
}

def categorize_line(line):
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return category
    return None

def process_files(input_dir, output_dir):
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
                confirm = input("Confirm move? (Y/N): ").strip().lower()
                if confirm == 'y':
                    with target_file.open('a', encoding='utf-8') as tf:
                        tf.write(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # Overwrite the original file with lines that weren't moved
        with file.open('w', encoding='utf-8') as f:
            f.writelines(new_lines)

if __name__ == "__main__":
    input_dir = input("Enter path to input directory: ").strip()
    output_dir = input("Enter path to target/output directory: ").strip()
    process_files(input_dir, output_dir)
