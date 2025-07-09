import monitor
from unittest.mock import patch, mock_open, MagicMock
import json

# --- Utility function tests ---
def test_load_json_file_returns_default_for_missing(tmp_path):
    missing_file = tmp_path / "missing.json"
    result = monitor.load_json_file(str(missing_file), default={"foo": 1})
    assert result == {"foo": 1}

def test_save_and_load_json_file(tmp_path):
    data = {"bar": 2}
    file_path = tmp_path / "test.json"
    monitor.save_json_file(str(file_path), data)
    loaded = monitor.load_json_file(str(file_path), default={})
    assert loaded == data

# --- Content hash tests ---
@patch("monitor.requests.get")
def test_get_content_hash_simple(mock_get):
    html = "<html><body><div id='main'>Hello World</div></body></html>"
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = html
    hash_val, content = monitor.get_content_hash("http://example.com", selector="#main")
    assert isinstance(hash_val, str)
    assert content is not None and "Hello World" in content

# --- RSS feed test ---
@patch("monitor.feedparser.parse")
def test_check_rss_feed_new_entry(mock_parse):
    entry = MagicMock()
    entry.id = "123"
    entry.title = "Test"
    entry.link = "url"
    entry.published = "now"
    entry.summary = "summary"
    entry.get = lambda key, default=None: {
        "title": "Test",
        "link": "url",
        "published": "now",
        "summary": "summary"
    }.get(key, default)
    mock_parse.return_value.entries = [entry]
    new_id, new_title, details = monitor.check_rss_feed("http://rss.com", last_entry_id=None)
    assert new_id == "123"
    assert new_title == "Test"
    assert details is not None and details["title"] == "Test"

# --- Main logic (smoke test) ---
def test_main_smoke(monkeypatch, tmp_path):
    # Patch file paths to use tmp_path
    monkeypatch.setattr(monitor, "URLS_FILE", str(tmp_path / "urls.json"))
    monkeypatch.setattr(monitor, "HASHES_FILE", str(tmp_path / "hashes.json"))
    monkeypatch.setattr(monitor, "CONTENT_FILE", str(tmp_path / "previous_content.json"))
    monkeypatch.setattr(monitor, "CHANGE_HISTORY_FILE", str(tmp_path / "change_history.json"))
    monkeypatch.setattr(monitor, "DOCS_DIR", str(tmp_path / "docs"))
    monkeypatch.setattr(monitor, "MARKDOWN_REPORT", str(tmp_path / "docs/index.md"))
    # Write a minimal urls.json
    urls = [{"url": "http://example.com"}]
    (tmp_path / "urls.json").write_text(json.dumps(urls))
    # Patch network call
    with patch("monitor.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "<html><body>Test</body></html>"
        monitor.main()
    # Check that output files were created
    assert (tmp_path / "hashes.json").exists()
    assert (tmp_path / "previous_content.json").exists()
    assert (tmp_path / "change_history.json").exists()
    assert (tmp_path / "docs/index.md").exists() 