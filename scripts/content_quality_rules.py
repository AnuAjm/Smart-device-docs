
import re


def check_duplicate_headings(file_path):
    """Find duplicate Markdown headings within a file."""
    headings = {}
    issues = []

    with open(file_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)

            if not match:
                continue

            level = len(match.group(1))
            heading_text = match.group(2).strip()
            normalized_heading = heading_text.casefold()

            key = (level, normalized_heading)

            if key in headings:
                issues.append({
                    "heading": heading_text,
                    "level": level,
                    "first_line": headings[key],
                    "duplicate_line": line_number,
                })
            else:
                headings[key] = line_number

    return issues
