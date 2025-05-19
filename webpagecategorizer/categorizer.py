import json
import re
from pathlib import Path
import click

def load_category_patterns(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Validate that data is in correct format
    if not isinstance(data, dict):
        raise ValueError("Category file must be a JSON object with category names as keys and list of regex patterns as values.")
    for key, patterns in data.items():
        if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
            raise ValueError(f"Each category must map to a list of regex strings. Problem in category: {key}")
    return data

def categorize_line(line, patterns_by_category):
    for category, patterns in patterns_by_category.items():
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return category
    return None

@click.command()
@click.option('--input-dir', '-i', required=True, type=click.Path(exists=True, file_okay=False), help='Directory with input .txt files.')
@click.option('--output-dir', '-o', required=True, type=click.Path(file_okay=False), help='Directory to write category files to.')
@click.option('--categories-file', '-c', required=True, type=click.Path(exists=True, dir_okay=False), help='Path to JSON file defining categories and regex patterns.')
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm all moves (non-interactive).')
@click.option('--remove-moved-lines', is_flag=True, help='Remove lines from source files based on lines moved into category files.')
def categorize_websites(input_dir, output_dir, categories_file, yes, remove_moved_lines):
    """Categorize websites into groups based on regex patterns from a JSON file."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load category patterns
    category_patterns = load_category_patterns(categories_file)

    all_moves = []  # List of tuples (file, line_num, line, category)

    # Step 1: Categorize lines
    for file in input_path.glob("*.txt"):
        with file.open('r', encoding='utf-8') as f:
            lines = f.readlines()

        for idx, line in enumerate(lines, 1):
            category = categorize_line(line, category_patterns)
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
        file_map = {}
        for file, idx, line, _ in all_moves:
            file_map.setdefault(file, []).append((idx, line))

        for file, removals in file_map.items():
            with file.open('r', encoding='utf-8') as f:
                lines = f.readlines()

            removal_indexes = {idx - 1 for idx, _ in removals}
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
