# __init__.py
import exrex
import re
import itertools
from typing import List

def generate_variants(pattern: str, custom_str: str = None) -> List[str]:
    """
    Generate all possible string variants based on the provided pattern.
    If custom_str is given, generate all variations of that string by interpreting character groups.
    If pattern is a strict regex, generate all matching strings.

    Args:
        pattern (str): The regex pattern or custom string with options.
        custom_str (str, optional): A custom string with brackets indicating options (e.g., 'a[bc]d').

    Returns:
        List[str]: A list of all generated string variants.
    """
    if custom_str:
        # Find all bracketed groups
        groups = re.findall(r'\[([^\]]+)\]', custom_str)
        # Generate Cartesian product of options
        options_lists = []
        last_index = 0
        parts = []
        for match in re.finditer(r'\[[^\]]+\]', custom_str):
            start, end = match.span()
            # Static part before bracket
            static_part = custom_str[last_index:start]
            parts.append([static_part])
            # Options inside brackets
            options = match.group(1)
            parts.append(list(options))
            last_index = end
        # Add the remaining static part after last bracket
        parts.append([custom_str[last_index:]])
        # Generate all combinations
        variants = [''.join(p) for p in itertools.product(*parts)]
        return variants
    else:
        # Use exrex to generate all matches of the regex pattern
        # Get all matches; exrex.getone returns one, exrex.generate returns all
        # We need to generate all possibilities
        return list(exrex.generate(pattern))