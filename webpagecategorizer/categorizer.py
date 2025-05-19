import json
import os.path
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Iterable

import click

LINKS_BY_CATEGORY: Dict[str, Set[str]] = {}

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


def get_links_from_file(category, target_file) -> Set[str]:
    if category in LINKS_BY_CATEGORY:
        return LINKS_BY_CATEGORY[category]

    if not os.path.exists(target_file):
        return set()
    with target_file.open('r', encoding='utf-8') as f:
        lines = f.readlines()

    s = set()
    for idx, line in enumerate(lines, 1):
        s.add(line)
    LINKS_BY_CATEGORY[category] = s

    return s


class LinkAction(ABC):
    @abstractmethod
    def perform(self):
        """Execute the action (e.g., copy or remove a line)."""
        pass

    @abstractmethod
    def describe(self) -> str:
        """Return a string describing the action (used for printing)."""
        pass


@dataclass
class RemoveLinksFromFileAction(LinkAction):
    category: str
    category_file: Path
    src_file_name: Path
    line_number: int
    links: Iterable[str] = field(default_factory=set)

    def perform(self):
        with self.src_file_name.open('r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped in self.links:
                continue
            new_lines.append(line)

        with self.src_file_name.open('w', encoding='utf-8') as f:
            f.writelines(new_lines)

    def describe(self) -> str:
        s = ""
        for link in self.links:
            s += f"{self.src_file_name}:{self.line_number} {link.strip()} --> REMOVED (from {self.category_file.name})\n"
        return s


@dataclass
class LinkCopyAction(LinkAction):
    category: str
    src_file_name: Path
    line_number: int
    link: str
    target_file: Path


    def perform(self):
        with self.target_file.open('a', encoding='utf-8') as f:
            f.write(self.link)

    def describe(self) -> str:
        return f"{self.src_file_name}:{self.line_number} {self.link.strip()} --> {self.target_file.name}"



class LinkActions:
    def __init__(self):
        self._actions: List[LinkAction] = []

    def add(self, action: LinkAction):
        self._actions.append(action)

    def size(self):
        return len(self._actions)

    def _get_actions_by_category(self):
        d: Dict[str, List[LinkAction]] = {}
        for a in self._actions:
            d.setdefault(a.category, []).append(a)
        return d

    def print_actions(self):
        actions_by_category = self._get_actions_by_category()

        for category, actions in actions_by_category.items():
            for action in actions:
                print(action.describe())

    def perform_actions(self):
        actions_by_category = self._get_actions_by_category()

        for category, actions in actions_by_category.items():
            for action in actions:
                action.perform()


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

    target_file_by_category = {}

    # Step 1: Categorize lines
    actions = LinkActions()
    for file in input_path.glob("*.txt"):
        with file.open('r', encoding='utf-8') as f:
            lines = f.readlines()

        for idx, line in enumerate(lines, 1):
            category = categorize_line(line, category_patterns)
            if category:
                if category not in target_file_by_category:
                    target_file_by_category[category] = output_path / f"{category}.txt"
                target_file = target_file_by_category[category]
                links = get_links_from_file(category, target_file)

                # Only add to target file if link does not exist
                if line not in links:
                    actions.add(LinkCopyAction(category, file, idx, line, target_file))

    actions.print_actions()
    if actions.size() > 0:
        if yes or click.confirm("Confirm line copy operations?"):
            actions.perform_actions()


    # Step 2: Optionally remove moved lines from original files
    if remove_moved_lines:
        remove_categorized_lines_from_inputs(input_path, output_path, yes)

def remove_categorized_lines_from_inputs(input_path, output_path, yes):
    """Removes lines from input files that already exist in the category files."""
    print("\n--- Removing lines from source files that are already in category files ---")

    # Step 1: Collect all categorized lines
    categorized_lines = set()
    for cat_file in output_path.glob("*.txt"):
        with cat_file.open('r', encoding='utf-8') as f:
            for line in f:
                categorized_lines.add(line.strip())

    actions = LinkActions()

    # Step 2: Remove matching lines from input files
    for file in input_path.glob("*.txt"):
        category = os.path.basename(file).replace(".txt", "")
        with file.open('r', encoding='utf-8') as f:
            lines = f.readlines()

        links = set()
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped in categorized_lines:
                links.add(stripped)

        if links:
            actions.add(RemoveLinksFromFileAction(category, cat_file, file, idx, links))

    actions.print_actions()
    if actions.size() > 0:
        if yes or click.confirm("Confirm line removal operations?"):
            actions.perform_actions()


if __name__ == '__main__':
    categorize_websites()
