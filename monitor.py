import json
import hashlib
import requests
import os
from bs4 import BeautifulSoup
from bs4.element import Tag
import difflib
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import feedparser

# === Configurable Constants ===
URLS_FILE: str = 'urls.json'
HASHES_FILE: str = 'hashes.json'
CONTENT_FILE: str = 'previous_content.json'
CHANGE_HISTORY_FILE: str = 'change_history.json'
DOCS_DIR: str = 'docs'
MARKDOWN_REPORT: str = os.path.join(DOCS_DIR, 'index.md')
LOGO_PATH: str = os.path.join(DOCS_DIR, 'logo.png')
PREVIEW_LENGTH: int = 100

# === Utility Functions ===
def load_json_file(path: str, default: Any) -> Any:
    """Load a JSON file or return a default value if it doesn't exist."""
    if not os.path.exists(path):
        return default
    with open(path, 'r') as f:
        return json.load(f)

def save_json_file(path: str, data: Any) -> None:
    """Save data to a JSON file with indentation."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_urls() -> List[Dict[str, Any]]:
    """Load the list of URLs and their config from the urls.json file."""
    return load_json_file(URLS_FILE, [])

def load_hashes() -> Dict[str, str]:
    """Load the hashes for all monitored sources."""
    return load_json_file(HASHES_FILE, {})

def save_hashes(hashes: Dict[str, str]) -> None:
    """Save the hashes for all monitored sources."""
    save_json_file(HASHES_FILE, hashes)

def load_previous_content() -> Dict[str, str]:
    """Load the previous content for all monitored URLs."""
    return load_json_file(CONTENT_FILE, {})

def save_previous_content(content: Dict[str, str]) -> None:
    """Save the previous content for all monitored URLs."""
    save_json_file(CONTENT_FILE, content)

def load_change_history() -> List[Dict[str, Any]]:
    """Load the change history log."""
    return load_json_file(CHANGE_HISTORY_FILE, [])

def save_change_history(history: List[Dict[str, Any]]) -> None:
    """Save the change history log."""
    save_json_file(CHANGE_HISTORY_FILE, history)

def append_change_history(entry: Dict[str, Any]) -> None:
    """Append a new entry to the change history log."""
    history = load_change_history()
    history.append(entry)
    save_change_history(history)

def human_date(dt: str) -> str:
    """Convert ISO datetime string to human-readable format."""
    try:
        d = datetime.datetime.fromisoformat(dt.replace('Z', '+00:00'))
        return d.strftime('%Y-%m-%d %H:%M UTC')
    except Exception:
        return dt

def generate_markdown_report() -> None:
    """Generate a Markdown report of recent and historical changes for GitHub Pages."""
    history = load_change_history()
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
    # Build a summary of the latest status for each monitored item
    summary: Dict[str, Dict[str, Any]] = {}
    first_seen = {}
    last_change = {}
    site_groups: Dict[str, List[str]] = {}
    for entry in history:
        # Use composite key for html-section, url for html, rss for feeds
        if entry['type'] == 'html-section':
            key = f"{entry['source']}::{entry.get('section','')}"
            label = entry.get('section','')
            site = entry['source']
        elif entry['type'] == 'html':
            key = entry['source']
            label = ''
            site = entry['source']
        elif entry['type'] == 'rss':
            key = entry['source']
            label = entry.get('title','')
            site = entry['source']
        else:
            key = entry['source']
            label = ''
            site = entry['source']
        # Track first seen
        if key not in first_seen:
            first_seen[key] = entry['timestamp']
        # Track last change (only if status is 'Changed')
        if entry['type'] in ['html-section', 'html', 'rss']:
            last_change[key] = entry['timestamp']
        # Always keep the most recent event for each key
        summary[key] = {
            'type': entry['type'],
            'source': entry['source'],
            'label': label,
            'last_checked': entry['timestamp'],
            'last_change': str(last_change.get(key, '')),
            'first_seen': first_seen[key],
            'status': 'Changed' if entry['type'] in ['html-section', 'html', 'rss'] else 'Checked',
            'preview': entry.get('preview','') if entry['type'] == 'html-section' else entry.get('summary','') if entry['type'] == 'rss' else ''
        }
        # Group by site
        if site not in site_groups:
            site_groups[site] = []
        if key not in site_groups[site]:
            site_groups[site].append(key)
    # Legend and latest update
    if history:
        latest_update = human_date(history[-1]['timestamp'])
    else:
        latest_update = "No updates yet"
    with open(MARKDOWN_REPORT, 'w') as f:
        if os.path.exists(LOGO_PATH):
            f.write(f'<img src="logo.png" alt="Kimchi Sentinel Logo" width="200"/>' + '\n\n')
        f.write('# 🥬 Kimchi Sentinel – Change Monitoring Dashboard\n\n')
        f.write(f'**Latest Update:** {latest_update}\n\n')
        f.write('---\n\n')
        f.write('## 🗺️ Legend\n')
        f.write('- 🟢 **Changed**: Content changed since last check\n')
        f.write('- ✅ **No Change**: No change detected\n')
        f.write('- 🔄 **First Check**: First time checking this item\n')
        f.write('- _Section/Feed_: For websites, the section or update block; for RSS, the feed entry title\n')
        f.write('- _Preview_: Snippet of the changed or monitored content\n')
        f.write('\n---\n\n')
        # Table of Contents
        f.write('## 📚 Table of Contents\n')
        for site in site_groups:
            f.write(f'- [{site}]({site})\n')
            for key in site_groups[site]:
                label = summary[key]['label']
                if label:
                    anchor = label.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('.', '').replace('/', '').replace(':', '').replace('–', '').replace('--', '-')
                    f.write(f'  - [{label}](#{anchor})\n')
        f.write('\n---\n\n')
        f.write('## 📊 Monitoring Summary\n\n')
        if not summary:
            f.write('No checks performed yet.\n')
        else:
            f.write('| Source | Section/Feed | First Seen | Last Checked | Last Change | Status | Preview |\n')
            f.write('|--------|--------------|------------|--------------|-------------|--------|---------|\n')
            for site in site_groups:
                for key in site_groups[site]:
                    item = summary[key]
                    src = f"[{item['source']}]({item['source']})"
                    label = item['label']
                    first_seen = human_date(item['first_seen'])
                    last_checked = human_date(item['last_checked'])
                    last_chg = human_date(item['last_change']) if item['last_change'] else '—'
                    status_icon = '🟢' if item['status'] == 'Changed' else '✅' if first_seen == last_checked else '🔄'
                    status = f"{status_icon} {item['status']}"
                    preview = item['preview'][:PREVIEW_LENGTH].replace('\n', ' ').replace('|', ' ')
                    f.write(f"| {src} | {label} | {first_seen} | {last_checked} | {last_chg} | {status} | {preview}{'...' if len(preview) == PREVIEW_LENGTH else ''} |\n")
        f.write('\n---\n\n')
        f.write('## 📝 Full Change History\n\n')
        if not history:
            f.write('No changes detected yet.\n')
        else:
            for entry in reversed(history):
                # Use descriptive heading
                if entry['type'] == 'html-section':
                    heading = f"{entry.get('section','')} – {entry['source']}"
                elif entry['type'] == 'html':
                    heading = f"{entry['source']}"
                elif entry['type'] == 'rss':
                    heading = f"{entry.get('title','')} – {entry['source']}"
                else:
                    heading = f"{entry['source']}"
                anchor = heading.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('.', '').replace('/', '').replace(':', '').replace('–', '').replace('--', '-')
                f.write(f"### {heading}\n<a name=\"{anchor}\"></a>\n")
                f.write(f"_Checked: {human_date(entry['timestamp'])}_  \n")
                if entry['type'] == 'rss':
                    f.write(f"**Type:** RSS Feed  \n")
                    f.write(f"**Title:** {entry.get('title','')}  \n")
                    if entry.get('published'):
                        f.write(f"**Published:** {entry['published']}  \n")
                    if entry.get('summary'):
                        f.write(f"> {entry.get('summary','').replace(chr(10), ' ')}  \n")
                elif entry['type'] == 'html-section':
                    f.write(f"**Type:** Website Section  \n")
                    f.write(f"**Section:** {entry.get('section','')}  \n")
                    f.write(f"> {entry.get('preview','')}  \n")
                elif entry['type'] == 'html':
                    f.write(f"**Type:** Website  \n")
                    f.write(f"> {entry.get('change','')}  \n")
                f.write('\n---\n\n')
        # Footer
        f.write('---\n')
        f.write('Powered by [Kimchi Sentinel](https://github.com/KimchiLegal/Kimchi-Sentinel) 🥬\n')

def show_diff(old_content: str, new_content: str, url: str) -> None:
    """Show a readable diff between old and new content for a URL."""
    print(f"\n🔍 CHANGES DETECTED for {url}:")
    print("=" * 80)
    old_lines = old_content.split('\n') if old_content else []
    new_lines = new_content.split('\n') if new_content else []
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile='Previous', tofile='Current',
        lineterm='', n=3
    )
    diff_text = '\n'.join(diff)
    if diff_text.strip():
        print(diff_text)
    else:
        print("Content changed but diff is not easily readable (possibly formatting changes)")
    print("=" * 80)

def get_content_hash(
    url: str,
    selector: Optional[str] = None,
    section_selector: Optional[str] = None,
    heading_selector: Optional[str] = None
) -> Tuple[Union[str, Dict[str, str], None], Optional[str]]:
    """
    Fetch and hash content from a URL.
    If section_selector and heading_selector are provided, extract and hash each section individually.
    Returns a dict of {heading: content} for sections, or a single hash and content for the whole page.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
        main_content = None
        # Dynamic section extraction if section_selector and heading_selector are provided
        if selector and section_selector and heading_selector:
            article = soup.select_one(selector)
            if article:
                updates = {}
                divs = article.select(section_selector)
                for div in divs:
                    if isinstance(div, Tag):
                        heading_tag = div.select_one(heading_selector)
                        if isinstance(heading_tag, Tag):
                            heading = heading_tag.get_text(strip=True)
                            section_html = str(heading_tag)
                            for sib in heading_tag.find_next_siblings():
                                section_html += str(sib)
                            section_text = BeautifulSoup(section_html, 'html.parser').get_text(separator=' ', strip=True)
                            updates[heading] = section_text
                return updates, None
        # Default behavior for other URLs
        if selector:
            selected = soup.select_one(selector)
            if isinstance(selected, Tag):
                for tag in selected.find_all(['script', 'nav', 'footer']):
                    tag.decompose()
                main_content = selected.get_text(separator=' ', strip=True)
        if not main_content:
            main_content = soup.get_text(separator=' ', strip=True)
        return hashlib.sha256(main_content.encode('utf-8')).hexdigest(), main_content
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None, None

def check_rss_feed(rss_url: str, last_entry_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, str]]]:
    """Check an RSS feed for new entries and return the latest entry ID, title, and details if new."""
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        return None, last_entry_id, None
    latest_entry = feed.entries[0]
    entry_id = str(getattr(latest_entry, 'id', '')) if hasattr(latest_entry, 'id') else ''
    entry_details = {
        'title': str(latest_entry.get('title', '') or ''),
        'link': str(latest_entry.get('link', '') or ''),
        'published': str(latest_entry.get('published', '') or ''),
        'summary': str(latest_entry.get('summary', '') or '')
    }
    if last_entry_id != entry_id:
        print(f"New RSS entry detected: {entry_details['title']} ({entry_details['link']})")
        return entry_id, entry_details['title'], entry_details
    return last_entry_id, None, entry_details

def main() -> None:
    """Main monitoring loop: checks all sources, logs changes, and generates the report."""
    url_entries = load_urls()
    old_hashes = load_hashes()
    old_content = load_previous_content()
    new_hashes: Dict[str, str] = {}
    new_content: Dict[str, str] = {}
    now = datetime.datetime.now(datetime.UTC).isoformat()
    for entry in url_entries:
        if isinstance(entry, dict) and 'rss' in entry:
            rss_url = entry['rss']
            last_id = old_hashes.get(rss_url)
            new_id, new_title, entry_details = check_rss_feed(rss_url, last_id)
            if new_title:
                print(f"Update found in RSS feed: {rss_url}")
                if entry_details:
                    append_change_history({
                        'timestamp': now,
                        'type': 'rss',
                        'source': rss_url,
                        'title': entry_details.get('title', ''),
                        'link': entry_details.get('link', ''),
                        'published': entry_details.get('published', ''),
                        'summary': entry_details.get('summary', '')
                    })
            if isinstance(new_id, str):
                new_hashes[rss_url] = new_id
            continue
        url = entry["url"] if isinstance(entry, dict) else entry
        selector = entry.get("selector") if isinstance(entry, dict) else None
        section_selector = entry.get("section_selector") if isinstance(entry, dict) else None
        heading_selector = entry.get("heading_selector") if isinstance(entry, dict) else None
        print(f"Checking {url} ...")
        result = get_content_hash(url, selector, section_selector, heading_selector)
        # Dynamic section extraction handling
        if section_selector and heading_selector and isinstance(result[0], dict):
            updates = result[0]
            for heading, section_text in updates.items():
                composite_key = f"{url}::{heading}"
                section_hash = hashlib.sha256(section_text.encode('utf-8')).hexdigest()
                if composite_key in old_hashes:
                    if old_hashes[composite_key] != section_hash:
                        print(f"CHANGE DETECTED: {url} [{heading}]")
                        append_change_history({
                            'timestamp': now,
                            'type': 'html-section',
                            'source': url,
                            'section': heading,
                            'preview': section_text[:500] + ("..." if len(section_text) > 500 else "")
                        })
                    else:
                        print(f"No change: {url} [{heading}]")
                else:
                    print(f"First time checking: {url} [{heading}]")
                    append_change_history({
                        'timestamp': now,
                        'type': 'html-section',
                        'source': url,
                        'section': heading,
                        'preview': section_text[:500] + ("..." if len(section_text) > 500 else "")
                    })
                new_hashes[composite_key] = section_hash
            continue
        # Default behavior for other URLs
        if result[0] is None:
            continue
        content_hash, current_content = result
        if isinstance(content_hash, str):
            if url in old_hashes:
                if old_hashes[url] != content_hash:
                    print(f"CHANGE DETECTED: {url}")
                    previous_content = old_content.get(url, "")
                    show_diff(previous_content, current_content or "", url)
                    append_change_history({
                        'timestamp': now,
                        'type': 'html',
                        'source': url,
                        'change': 'Content changed'
                    })
                else:
                    print(f"No change: {url}")
            else:
                print(f"First time checking: {url}")
                append_change_history({
                    'timestamp': now,
                    'type': 'html',
                    'source': url,
                    'change': 'First time checking'
                })
            new_hashes[url] = content_hash
        if isinstance(current_content, str):
            new_content[url] = current_content
    save_hashes(new_hashes)
    save_previous_content(new_content)
    generate_markdown_report()

if __name__ == "__main__":
    main() 