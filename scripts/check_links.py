
from pathlib import Path
from urllib.parse import urlparse
import re
import sys
import requests

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
TIMEOUT = 10

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


if __name__ == "__main__":
    (
        files_scanned,
        links_checked,
        broken_local,
        broken_external
    ) = check_markdown_links()

    print("\nDOCUMENTATION LINK QA REPORT")
    print("=" * 35)
    print(f"Markdown files scanned: {files_scanned}")
    print(f"Links checked: {links_checked}")
    print(f"Broken local links: {len(broken_local)}")
    print(f"Broken external links: {len(broken_external)}")

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

    if broken_local or broken_external:
        print("RESULT: FAILED - Broken links detected.")
        sys.exit(1)

    print("\nRESULT: PASSED - No broken links found.")
    sys.exit(0)
