# Tutorial: Building an Image Crawler

> 📅 Last Updated: 2026/09/09

This tutorial will guide you through a complete hands-on project — **Baidu Image Crawler** — to learn CelestialFlow from scratch.

## Project Goal

Crawl Baidu image search results and download images for specified keywords to your local machine. We will learn how to:
1. Analyze and decompose the task flow
2. Write processing functions for each stage
3. Assemble and run the task graph
4. Monitor execution status via logs, progress bar and status snapshots

---

## Step 1: Task Analysis and Decomposition

Before coding, we need to analyze the crawler's execution flow:

```
User inputs keyword → Search page → Parse image list → Download images → Save files
```

### Task Layer Design

| Layer | Function | Input | Output |
|------|------|------|------|
| **Layer 1: Search** | Fetch search result page | Keyword | Page HTML |
| **Layer 2: Parse** | Extract image URL list | HTML | Image URL list |
| **Layer 3: Download** | Download image content | Image URL | Image binary data |
| **Layer 4: Store** | Save to local disk | Image data | File path |

### Task Graph Structure

```mermaid
flowchart LR
    subgraph TG[Image Crawler Task Graph]
        direction LR
        
        S1[Search Page]
        S2[Parse Images]
        S3[Download Images]
        S4[Store Files]
        
        S1 --> S2
        S2 --> S3
        S3 --> S4
    end
    
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;
    class S1,S2,S3,S4 blueNode;
```

---

## Step 2: Write Processing Functions

First, write the processing functions for each stage and test them individually.

### 2.1 Search Page

```python
import requests
from urllib.parse import quote


def search_images(keyword: str) -> str:
    """
    Search Baidu images by keyword and return page HTML.

    :param keyword: Search keyword
    :return: Page HTML content
    """
    url = f"https://image.baidu.com/search/index?tn=baiduimage&word={quote(keyword)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


# Standalone test
if __name__ == "__main__":
    html = search_images("cat")
    print(f"Fetched {len(html)} characters of HTML")
```

### 2.2 Parse Image URLs

```python
import re
import json


def parse_image_urls(html: str) -> list[str]:
    """
    Parse image URL list from HTML.

    :param html: Page HTML
    :return: List of image URLs
    """
    # Baidu image data is embedded in JavaScript
    pattern = r'"hoverURL":"(https?://[^"]+)"'
    urls = re.findall(pattern, html)
    # Handle escape characters
    urls = [url.replace("\\/", "/") for url in urls]
    return urls[:20]  # Limit quantity


# Standalone test
if __name__ == "__main__":
    html = search_images("cat")
    urls = parse_image_urls(html)
    print(f"Parsed {len(urls)} image URLs")
    for url in urls[:3]:
        print(f"  - {url}")
```

### 2.3 Download Images

```python
import time


def download_image(url: str) -> bytes | None:
    """
    Download image content.

    :param url: Image URL
    :return: Image binary data, None on failure
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://image.baidu.com/",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Download failed: {url}, error: {e}")
        return None


# Standalone test
if __name__ == "__main__":
    html = search_images("cat")
    urls = parse_image_urls(html)
    if urls:
        data = download_image(urls[0])
        if data:
            print(f"Download successful, size: {len(data)} bytes")
```

### 2.4 Store Files

```python
import os
import hashlib


def save_image(image_data: bytes, keyword: str) -> str:
    """
    Save image to local disk.

    :param image_data: Image binary data
    :param keyword: Keyword (used to create directory)
    :return: Saved file path
    """
    # Create directory
    save_dir = os.path.join("images", keyword)
    os.makedirs(save_dir, exist_ok=True)

    # Use data hash as filename
    file_hash = hashlib.md5(image_data).hexdigest()[:12]
    file_path = os.path.join(save_dir, f"{file_hash}.jpg")

    # Avoid duplicate downloads
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(image_data)

    return file_path


# Standalone test
if __name__ == "__main__":
    html = search_images("cat")
    urls = parse_image_urls(html)
    if urls:
        data = download_image(urls[0])
        if data:
            path = save_image(data, "cat")
            print(f"Saved successfully: {path}")
```

---

## Step 3: Assemble the Task Graph

After verifying the processing functions, assign them to their respective `TaskExecutor` nodes and organize them with `TaskGraph`.

### 3.1 Create Nodes

```python
from celestialflow import TaskExecutor, TaskSplitter

# Search stage: input keyword, output HTML
stage_search = TaskExecutor(
    "Search Page",
    func=search_images,
    execution_mode="serial",  # Only one keyword, serial is sufficient
    max_retries=2,
)


# Parse stage: input HTML, output multiple image URLs (needs splitting)
# Need a custom Splitter to split the URL list
class URLSplitter(TaskSplitter):
    """Split URL list into individual tasks."""

    def _split(self, html: str):
        urls = parse_image_urls(html)
        print(f"Parsed {len(urls)} image URLs")
        return tuple(urls)


stage_parse = URLSplitter("Parse Images")

# Download stage: input URL, output image data
stage_download = TaskExecutor(
    "Download Images",
    func=download_image,
    execution_mode="thread",  # Network I/O intensive, use thread pool
    max_workers=10,  # Download 10 concurrently
    max_retries=3,
)

# Store stage: input image data, output file path
stage_save = TaskExecutor(
    "Store Files",
    func=lambda data: save_image(data, "cat") if data else None,
    execution_mode="serial",
    enable_duplicate_check=False,  # Allow saving duplicate data (for retries)
)
```

### 3.2 Build the Task Graph

```python
from celestialflow import TaskGraph

# Create task graph
graph = TaskGraph(name="ImageCrawler", graph_mode="eager", log_level="SUCCESS")

# Set nodes
graph.set_nodes(stages=[stage_search, stage_parse, stage_download, stage_save])

# Set connection relationships between nodes
graph.connect([stage_search], [stage_parse])
graph.connect([stage_parse], [stage_download])
graph.connect([stage_download], [stage_save])
```

### 3.3 Enable Status Reporting (Optional)

```python
# Report running status to the celestialflow-web service
graph.set_reporter(TaskReporter(report_host, report_port, graph))
```

The main repo no longer includes a built-in Web service. If you have an independently deployed `celestialflow-web` project or a custom HTTP service, you can enable reporting here; otherwise you can skip this section.

### 3.4 Run the Task Graph

```python
# Prepare initial tasks
init_tasks = {stage_search.get_name(): ["cat", "dog", "scenery"]}

# Start
print("Starting image crawl...")
graph.run(init_tasks)
```

---

## Step 4: Complete Code

Combine all code into a single file:

```python
# crawler.py
import os
import re
import hashlib
import requests
from urllib.parse import quote

from celestialflow import (
    TaskExecutor,
    TaskSplitter,
    TaskGraph,
    TaskReporter,
)

# ========== Processing Functions ==========


def search_images(keyword: str) -> str:
    """Search Baidu images."""
    url = f"https://image.baidu.com/search/index?tn=baiduimage&word={quote(keyword)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


def parse_image_urls(html: str) -> list[str]:
    """Parse image URLs."""
    pattern = r'"hoverURL":"(https?://[^"]+)"'
    urls = re.findall(pattern, html)
    return [url.replace("\\/", "/") for url in urls][:20]


def download_image(url: str) -> bytes | None:
    """Download image."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://image.baidu.com/",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception:
        return None


def save_image(image_data: bytes, keyword: str) -> str | None:
    """Save image."""
    if not image_data:
        return None
    save_dir = os.path.join("images", keyword)
    os.makedirs(save_dir, exist_ok=True)
    file_hash = hashlib.md5(image_data).hexdigest()[:12]
    file_path = os.path.join(save_dir, f"{file_hash}.jpg")
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(image_data)
    return file_path


# ========== Custom Node ==========


class URLSplitter(TaskSplitter):
    """URL list splitter."""

    def _split(self, html: str):
        urls = parse_image_urls(html)
        print(f"Parsed {len(urls)} image URLs")
        return tuple(urls)


# ========== Build Task Graph ==========


def build_crawler_graph(keyword: str) -> TaskGraph:
    """Build crawler task graph."""

    # Create nodes
    stage_search = TaskExecutor(
        "Search Page",
        func=search_images,
        execution_mode="serial",
        max_retries=2,
    )

    stage_parse = URLSplitter("Parse Images")

    stage_download = TaskExecutor(
        "Download Images",
        func=download_image,
        execution_mode="thread",
        max_workers=10,
        max_retries=3,
    )

    # Use closure to pass keyword
    stage_save = TaskExecutor(
        "Store Files",
        func=lambda data: save_image(data, keyword),
        execution_mode="serial",
        enable_duplicate_check=False,
    )

    # Set connections
    graph = TaskGraph(name="ImageCrawler", graph_mode="eager", log_level="SUCCESS")
    graph.set_nodes(stages=[stage_search, stage_parse, stage_download, stage_save])
    graph.connect([stage_search], [stage_parse])
    graph.connect([stage_parse], [stage_download])
    graph.connect([stage_download], [stage_save])

    return graph


# ========== Main ==========

if __name__ == "__main__":
    # Configuration
    KEYWORDS = ["cat", "dog", "scenery"]

    # Build graph
    graph = build_crawler_graph(KEYWORDS[0])

    # Run
    print("Starting image crawl...")
    graph.run({"Search Page": KEYWORDS})

    # Statistics
    print(f"\nCrawl complete!")
    print(f"Success: {stage_search.get_counts()['tasks_succeeded']}")
    print(f"Failed: {stage_search.get_counts()['tasks_failed']}")
```

---

## Step 5: Run and Debug

### 5.1 Run the Crawler

```bash
# Run the crawler
python crawler.py
```

### 5.2 View Running Status

During execution, you can monitor through logs, progress bar, or node `snapshot()` snapshots:

1. **Node Processing Progress**: Success, failure, and pending statistics for each stage (obtained via `get_counts()` or `snapshot()`)
2. **Graph Structure Information**: View via `graph.get_structure_list()` or `graph.get_structure_graph()`
3. **Error Information**: Failed image URLs and exception logs
4. **Task Injection**: Continue injecting new keywords via `node.put_task()`, or inject a termination signal via `node.put_signal()`

### 5.3 View Results

```bash
# View downloaded images
ls images/cat/
ls images/dog/
ls images/scenery/
```

---

## Extension: Dynamic Task Injection

You can also dynamically inject new keywords via code:

```python
# Or inject via code
from celestialflow import TerminationSignal

# Inject new keywords
for keyword in ["car", "food"]:
    stage_search.put_task(keyword)

# Inject termination signal (stop crawling)
stage_search.put_signal()
```

---

## Summary

This tutorial demonstrated the complete workflow of using CelestialFlow:

1. **Task Analysis**: Decompose complex tasks into independent layers
2. **Function Writing**: Write processing functions for each layer and test individually
3. **Node Creation**: Wrap functions as `TaskExecutor`
4. **Graph Assembly**: Organize node relationships with `TaskGraph`
5. **Monitor & Run**: Monitor execution status via logs, progress bar, and status snapshots

### Key Concept Review

| Concept | Description |
|------|------|
| `TaskExecutor` | Task node, wrapping a processing function |
| `TaskSplitter` | Splitter, splitting one task into multiple |
| `TaskGraph` | Task graph, organizing node relationships and execution flow |
| `graph_mode` | Graph running mode (serial/thread) |
| `execution_mode` | Node internal execution mode (serial/thread/async) |

### Next Steps

- Try using `TaskRouter` for conditional dispatching
- Refer to `demo/demo_redis.py` to learn how to integrate Redis / Go Worker collaboration using ordinary `TaskExecutor`
- Read other [API References](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/node/core_node.md) to learn more features
