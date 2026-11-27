
from pathlib import Path
import re

# Required components for each safety-message type.
SAFETY_MESSAGE_RULES = {
    "DANGER": [
        "Hazard",
        "Consequence",
        "Avoidance",
    ],
    "WARNING": [
        "Hazard",
        "Consequence",
        "Avoidance",
    ],
    "NOTICE": [
        "Situation",
        "Consequence",
        "Avoidance",
    ],
}


def validate_safety_message(message_type, message_text):
    """Validate the required components of a safety message."""
    issues = []

    message_type = message_type.upper()

    if message_type not in SAFETY_MESSAGE_RULES:
        return [f"Unsupported safety-message type: {message_type}"]

    for component in SAFETY_MESSAGE_RULES[message_type]:
        pattern = rf"^\*\*{re.escape(component)}:\*\*"

        if not re.search(pattern, message_text, re.MULTILINE):
            issues.append(f"Missing required component: {component}")

    return issues


def validate_safety_file(file_path):
    """Read and validate safety messages in a Markdown file."""
    content = Path(file_path).read_text(encoding="utf-8")

    message_pattern = re.compile(
        r"^##\s+\d+\.\s+(DANGER|WARNING|NOTICE)\s*$",
        re.MULTILINE | re.IGNORECASE
    )

    matches = list(message_pattern.finditer(content))
    file_issues = []

    for index, match in enumerate(matches):
        message_type = match.group(1).upper()
        start = match.end()

        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(content)
        )

        message_text = content[start:end]
        issues = validate_safety_message(message_type, message_text)

        for issue in issues:
            file_issues.append({
                "message_type": message_type,
                "issue": issue,
                "line": content.count("\n", 0, start) + 1,
            })

    return file_issues
