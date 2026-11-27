
from pathlib import Path
from urllib.parse import urlparse
import re
import sys
import requests
from terminology_rules import PREFERRED_TERMS, PROHIBITED_TERMS
from measurement_rules import check_measurement_spacing
from safety_rules import validate_safety_file

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
TIMEOUT = 10
REQUIRED_HEADINGS = {
    "industrial/installation.md": [
        "1. Overview",
        "2. Prerequisites",
        "3. Safety Information",
        "4. Installation Procedure",
        "5. Verification",
        "6. Troubleshooting",
        "7. Related Documentation",
    ],

    "industrial/configuration.md": [
        "1. Overview",
        "2. Prerequisites",
        "3. Configuration Procedure",
        "4. Verification",
        "5. Troubleshooting",
        "6. Related Documentation",
    ],
}

MARKDOWN_LINK_PATTERN = re.compile(
    r"\[[^\]]+\]\((https?://[^)\s]+|[^)\s]+)\)"
)

PLAIN_URL_PATTERN = re.compile(r"https?://[^\s<>()]+")


def extract_links(content):
    """Extract Markdown links and plain URLs without duplicates."""
    markdown_links = MARKDOWN_LINK_PATTERN.findall(content)
    plain_urls = PLAIN_URL_PATTERN.findall(content)

    links = markdown_links + plain_urls

    return list(dict.fromkeys(links))


def check_external_link(url):
    """Check whether an external URL is reachable."""
    try:
        response = requests.head(
            url,
            allow_redirects=True,
            timeout=TIMEOUT
        )

        if response.status_code in (403, 405):
            response = requests.get(
                url,
                allow_redirects=True,
                timeout=TIMEOUT,
                stream=True
            )

        if response.status_code >= 400:
            return f"HTTP {response.status_code}"

        return None

    except requests.RequestException as error:
        return str(error)
def check_required_headings():
    """Check required headings across configured documentation files."""
    heading_issues = []

    for relative_path, required_headings in REQUIRED_HEADINGS.items():
        document_path = DOCS_DIR / relative_path

        if not document_path.exists():
            heading_issues.append(
                (relative_path, "Document file not found")
            )
            continue

        content = document_path.read_text(encoding="utf-8")

        headings = set(
            re.findall(
                r"^#{1,6}\s+(.+?)\s*#*\s*$",
                content,
                re.MULTILINE
            )
        )

        for heading in required_headings:
            if heading not in headings:
                heading_issues.append((relative_path, heading))

    return heading_issues


def check_terminology():
    """Check documentation for inconsistent and prohibited terminology."""
    terminology_issues = []

    for markdown_file in DOCS_DIR.rglob("*.md"):
        content = markdown_file.read_text(encoding="utf-8")
        relative_path = markdown_file.relative_to(DOCS_DIR)

        for line_number, line in enumerate(content.splitlines(), start=1):

            for incorrect_term, preferred_term in PREFERRED_TERMS.items():
                pattern = rf"\b{re.escape(incorrect_term)}\b"

                for match in re.finditer(pattern, line, re.IGNORECASE):
                    terminology_issues.append(
                        (
                            relative_path,
                            line_number,
                            match.group(),
                            preferred_term,
                            "Use preferred terminology"
                        )
                    )

            for prohibited_term in PROHIBITED_TERMS:
                pattern = rf"\b{re.escape(prohibited_term)}\b"

                for match in re.finditer(pattern, line, re.IGNORECASE):
                    terminology_issues.append(
                        (
                            relative_path,
                            line_number,
                            match.group(),
                            "",
                            "Review prohibited wording"
                        )
                    )

    return terminology_issues


def check_markdown_links():
    broken_local_links = []
    broken_external_links = []

    files_scanned = 0
    links_checked = 0

    for markdown_file in DOCS_DIR.rglob("*.md"):
        files_scanned += 1

        content = markdown_file.read_text(encoding="utf-8")
        links = extract_links(content)

        for link in links:
            link = link.strip().rstrip(".,;:")

            if link.startswith(("mailto:", "#")):
                continue

            links_checked += 1

            if link.startswith(("http://", "https://")):
                reason = check_external_link(link)

                if reason:
                    broken_external_links.append(
                        (markdown_file, link, reason)
                    )

                continue

            link_path = link.split("#")[0]

            if not link_path:
                continue

            target = (markdown_file.parent / link_path).resolve()

            if not target.exists():
                broken_local_links.append(
                    (markdown_file, link)
                )

    return (
        files_scanned,
        links_checked,
        broken_local_links,
        broken_external_links
    )

def check_measurements():
    """Check documentation for measurement spacing issues."""
    measurement_issues = []

    for markdown_file in DOCS_DIR.rglob("*.md"):
        content = markdown_file.read_text(encoding="utf-8")
        relative_path = markdown_file.relative_to(DOCS_DIR)

        for line_number, line in enumerate(content.splitlines(), start=1):
            issues = check_measurement_spacing(line)

            for issue in issues:
                measurement_issues.append(
                    (
                        relative_path,
                        line_number,
                        issue["value"],
                        issue["preferred"],
                    )
                )

    return measurement_issues


def check_safety_messages():
    """Validate required components in the safety-message document."""
    safety_file = DOCS_DIR / "industrial" / "safety-messages.md"

    if not safety_file.exists():
        return [(safety_file, "Safety document not found")]

    issues = validate_safety_file(safety_file)

    return [
        (safety_file, issue)
        for issue in issues
    ]

if __name__ == "__main__":
    (
        files_scanned,
        links_checked,
        broken_local,
        broken_external
    ) = check_markdown_links()

    missing_headings = check_required_headings()
    terminology_issues = check_terminology()
    measurement_issues = check_measurements()
    safety_issues = check_safety_messages()

    print("\nDOCUMENTATION QA REPORT")
    print("=" * 35)
    print(f"Markdown files scanned: {files_scanned}")
    print(f"Links checked: {links_checked}")
    print(f"Broken local links: {len(broken_local)}")
    print(f"Broken external links: {len(broken_external)}")
    print(f"Missing required headings: {len(missing_headings)}")
    print(f"Terminology issues: {len(terminology_issues)}")
    print(f"Measurement formatting issues: {len(measurement_issues)}")
    print(f"Safety-message issues: {len(safety_issues)}")

    if missing_headings:
        print("\nMISSING REQUIRED HEADINGS")
        for file_path, heading in missing_headings:
            print(f"File: {file_path}")
            print(f"Missing: {heading}\n")

    if terminology_issues:
        print("\nTERMINOLOGY ISSUES")
        for file_path, line_number, found_term, preferred_term, issue_type in terminology_issues:
            print(f"File: {file_path}")
            print(f"Line: {line_number}")
            print(f"Found: {found_term}")
            if preferred_term:
                print(f"Preferred term: {preferred_term}")
            print(f"Issue: {issue_type}\n")

    if measurement_issues:
        print("\nMEASUREMENT FORMATTING ISSUES")
        for file_path, line_number, found_value, preferred_value in measurement_issues:
            print(f"File: {file_path}")
            print(f"Line: {line_number}")
            print(f"Found: {found_value}")
            print(f"Preferred format: {preferred_value}\n")

    if safety_issues:
        print("\nSAFETY-MESSAGE ISSUES")
        for file_path, issue in safety_issues:
            print(f"File: {file_path.relative_to(DOCS_DIR)}")
            if isinstance(issue, dict):
                print(f"Message type: {issue['message_type']}")
                print(f"Section heading line: {issue['line']}")
                print(f"Issue: {issue['issue']}\n")
            else:
                print(f"Issue: {issue}\n")

    if broken_local:
        print("\nBROKEN LOCAL LINKS")
        for source_file, link in broken_local:
            print(f"{source_file.relative_to(DOCS_DIR)}: {link}")

    if broken_external:
        print("\nBROKEN EXTERNAL LINKS")
        for source_file, link, reason in broken_external:
            print(f"File: {source_file.relative_to(DOCS_DIR)}")
            print(f"Link: {link}")
            print(f"Reason: {reason}\n")

    if (
        broken_local
        or broken_external
        or missing_headings
        or terminology_issues
        or measurement_issues
        or safety_issues
    ):
        print("\nRESULT: FAILED - Documentation QA issues detected.")

        if broken_local or broken_external:
            print("- Link validation failed.")
        if missing_headings:
            print("- Required heading validation failed.")
        if terminology_issues:
            print("- Terminology validation failed.")
        if measurement_issues:
            print("- Measurement formatting validation failed.")
        if safety_issues:
            print("- Safety-message validation failed.")

        sys.exit(1)

    print("\nRESULT: PASSED - All documentation QA checks passed.")
    sys.exit(0)
