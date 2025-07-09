# 🥬 Kimchi Sentinel

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Last Update](https://img.shields.io/github/last-commit/KimchiLegal/Kimchi-Sentinel?label=last%20update)
[![Build](https://github.com/KimchiLegal/Kimchi-Sentinel/actions/workflows/sentinel.yml/badge.svg)](https://github.com/KimchiLegal/Kimchi-Sentinel/actions/workflows/sentinel.yml)

**Kimchi Sentinel** is a flexible, open-source monitoring tool for tracking changes on privacy law and regulatory websites, as well as their RSS feeds. It generates a beautiful, human-readable dashboard (Markdown report) that can be published via GitHub Pages or viewed locally.

---

## 🚀 Features

- **Monitor any website or RSS feed** for content changes
- **Section-based extraction**: Track updates to specific sections (e.g., news, updates, blog posts) using CSS selectors
- **RSS feed support**: Detect and summarize new entries
- **Readable Markdown dashboard**: See recent and historical changes at a glance
- **Easy configuration**: Add new sites or feeds by editing a JSON file
- **Change previews**: See a snippet of what changed, not just that something changed
- **No hardcoding**: All extraction logic is configurable per site
- **Ready for GitHub Pages**: Publish your dashboard as a live website

---

## 📦 Setup

1. **Clone the repository**
   ```sh
   git clone https://github.com/KimchiLegal/Kimchi-Sentinel.git
   cd Kimchi-Sentinel
   ```
2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
3. **(Optional) Set up a virtual environment**
   ```sh
   python -m venv venv
   source venv/bin/activate
   ```

---

## ⚙️ Configuration

Edit `urls.json` to specify the sites and feeds you want to monitor. Example:
```json
[
  {
    "url": "https://autoriteitpersoonsgegevens.nl/over-deze-website/wijzigingen-op-deze-website",
    "selector": "article.node-page-full",
    "section_selector": "div.paragraph-text-lane__body-item.text-basic-html",
    "heading_selector": "h2"
  },
  {
    "rss": "https://edpb.europa.eu/feed/news_en"
  }
]
```
- `url`: The page to monitor
- `selector`: Main content area (CSS selector)
- `section_selector`: (Optional) CSS selector for update/news sections
- `heading_selector`: (Optional) CSS selector for section headings
- `rss`: RSS feed URL to monitor

---

## 🛠️ Usage

Run the monitor:
```sh
python monitor.py
```
- The script will check all configured sources, log any changes, and update the Markdown dashboard in `docs/index.md`.
- The first run will log the current state of all sections and feeds.

---

## 📊 Output & Reporting

- **Markdown dashboard**: See `docs/index.md` for a live summary and full change history.
- **GitHub Pages**: Enable Pages in your repo settings, set the source to `/docs`, and your dashboard will be published at `https://<username>.github.io/<repo>/`.
- **Change history**: All events are logged in `change_history.json`.

---

## 🧩 Extensibility

- Add new sites or feeds by editing `urls.json`—no code changes needed.
- Supports any site structure via configurable selectors.
- Easily extend to support notifications, more output formats, or a web UI.

---

## 🤝 Contributing

Contributions are welcome! To propose a change:
1. Fork the repo
2. Create a new branch
3. Make your changes (with clear commit messages)
4. Open a pull request

Please ensure your code is clean, documented, and tested.

---

## 📄 License

This project is licensed under the MIT License.

---

## 💡 Example Use Cases
- Track regulatory updates from privacy authorities
- Monitor news or blog sections for new posts
- Watch for changes in legal guidance or documentation

---

**Kimchi Sentinel** – Stay on top of privacy law changes, effortlessly. 

## Example Output Files

After running `monitor.py` for the first time, you will see these files generated/updated:

### hashes.json
```json
{
  "https://example.com": "a1b2c3d4e5f6...",
  "https://another.com::Section Name": "f7e8d9c0b1a2..."
}
```

### previous_content.json
```json
{
  "https://example.com": "Full text content of the page...",
  "https://another.com::Section Name": "Section content..."
}
```

### change_history.json
```json
[
  {
    "timestamp": "2024-06-10T07:00:00+00:00",
    "type": "html",
    "source": "https://example.com",
    "change": "First time checking"
  },
  {
    "timestamp": "2024-06-10T07:00:00+00:00",
    "type": "html-section",
    "source": "https://another.com",
    "section": "Section Name",
    "preview": "Section content preview..."
  }
]
```

These files are used to track the state and history of monitored web pages and are automatically updated by the monitoring script. 