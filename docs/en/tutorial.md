# Tutorial: Building an Image Crawler

> 📅 Last updated: 2026/04/22

This tutorial will walk you through learning CelestialFlow from scratch using a complete hands-on project — a **Baidu Image Crawler**.

## Project Goals

Crawl Baidu Image search results and download images for specified keywords to the local machine. We will learn how to:
1. Analyze the task flow and break it down
2. Write processing functions for each stage
3. Assemble the task graph and run it
4. Monitor execution status through the Web UI

---

## Step 1: Task Analysis and Decomposition

Before coding, we need to analyze the crawler's execution flow:

```
User inputs keyword → Search page → Parse image list → Download images → Save files
```

### Task Layer Design

| Layer | Function | Input | Output |
|-------|----------|-------|--------|
| **Layer 1: Search** | Fetch search result page | Keyword | Page HTML |
| **Layer 2: Parse** | Extract image URL list | HTML | Image URL list |
| **Layer 3: Download** | Download image content | Image URL | Image binary data |
| **Layer 4: Storage** | Save to local disk | Image data | File path |

### Task Graph Structure

```mermaid
flowchart LR
    subgraph TG[Image Crawler Task Graph]
        direction LR
        
        S1[Search Page]
        S2[Parse Images]
        S3[Download Images]
        S4[Save Files]
        
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

We will first write the processing functions for each stage and test them individually.

### 2.1 Search Page

```python
import requests
from urllib.parse import quote

def search_images(keyword: str) -> str:
    """
    Search Baidu Images by keyword and return the page HTML.
    
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
    html = search_images("猫咪")
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
    :return: Image URL list
    """
    # Baidu Images data is embedded in JavaScript
    pattern = r'"hoverURL":"(https?://[^"]+)"'
    urls = re.findall(pattern, html)
    # Handle escape characters
    urls = [url.replace("\\/", "/") for url in urls]
    return urls[:20]  # Limit quantity

# Standalone test
if __name__ == "__main__":
    html = search_images("猫咪")
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
    :return: Image binary data, or None on failure
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://image.baidu.com/"
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
    html = search_images("猫咪")
    urls = parse_image_urls(html)
    if urls:
        data = download_image(urls[0])
        if data:
            print(f"Download successful, size: {len(data)} bytes")
```

### 2.4 Save Files

```python
import os
import hashlib

def save_image(image_data: bytes, keyword: str) -> str:
    """
    Save an image to local disk.
    
    :param image_data: Image binary data
    :param keyword: Keyword (used for creating directory)
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
    html = search_images("猫咪")
    urls = parse_image_urls(html)
    if urls:
        data = download_image(urls[0])
        if data:
            path = save_image(data, "猫咪")
            print(f"Saved successfully: {path}")
```

---

## Step 3: Assemble the Task Graph

After verifying the processing functions, we assign them to their respective `TaskStage` instances, then organize the structure with `TaskGraph`.

### 3.1 Create Nodes

```python
from celestialflow import TaskStage, TaskSplitter

# Search stage: input keyword, output HTML
stage_search = TaskStage(
    func=search_images,
    execution_mode="serial",  # Only one keyword, serial is sufficient
    max_retries=2,
)

# Parse stage: input HTML, output multiple image URLs (requires splitting)
# A custom Splitter is needed to split the URL list
class URLSplitter(TaskSplitter):
    """Split URL list into multiple independent tasks."""
    
    def _split(self, html: str):
        urls = parse_image_urls(html)
        print(f"Parsed {len(urls)} image URLs")
        return tuple(urls)

stage_parse = URLSplitter()

# Download stage: input URL, output image data
stage_download = TaskStage(
    func=download_image,
    execution_mode="thread",  # Network IO intensive, use thread pool
    worker_limit=10,          # Download 10 images concurrently
    max_retries=3,
)

# Save stage: input image data, output file path
stage_save = TaskStage(
    func=lambda data: save_image(data, "猫咪") if data else None,
    execution_mode="serial",
    enable_duplicate_check=False,  # Allow saving duplicate data (for retries)
)
```

### 3.2 Build the Task Graph

```python
from celestialflow import TaskGraph

# Create task graph
graph = TaskGraph(schedule_mode="eager", log_level="SUCCESS")

# Set up nodes
graph.set_stages(root_stages=[stage_search], stages=[stage_parse, stage_download, stage_save])

# Set up connections between nodes
graph.connect([stage_search], [stage_parse])
graph.connect([stage_parse], [stage_download])
graph.connect([stage_download], [stage_save])
```

### 3.3 Start Web Monitoring (Optional)

```python
# Enable Web monitoring
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

Start the Web service:
```bash
celestialflow-web --port 5005
```

Visit http://localhost:5005 to view real-time status.

### 3.4 Run the Task Graph

```python
# Prepare initial tasks
init_tasks = {
    stage_search.get_tag(): ["猫咪", "小狗", "风景"]
}

# Start
print("Starting image crawl...")
graph.start_graph(init_tasks)

# Get statistics
print(f"Succeeded: {graph.get_graph_summary().get('total_successed', 0)}")
print(f"Failed: {graph.get_graph_summary().get('total_failed', 0)}")
```

---

## Step 4: Complete Code

Integrate all the code into a single file:

```python
# crawler.py
import os
import re
import hashlib
import requests
from urllib.parse import quote

from celestialflow import (
    TaskStage, 
    TaskSplitter, 
    TaskGraph,
)

# ========== Processing Functions ==========

def search_images(keyword: str) -> str:
    """Search Baidu Images."""
    url = f"https://image.baidu.com/search/index?tn=baiduimage&word={quote(keyword)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text

def parse_image_urls(html: str) -> list[str]:
    """Parse image URLs."""
    pattern = r'"hoverURL":"(https?://[^"]+)"'
    urls = re.findall(pattern, html)
    return [url.replace("\\/", "/") for url in urls][:20]

def download_image(url: str) -> bytes | None:
    """Download an image."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://image.baidu.com/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception:
        return None

def save_image(image_data: bytes, keyword: str) -> str | None:
    """Save an image."""
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

# ========== Custom Nodes ==========

class URLSplitter(TaskSplitter):
    """URL list splitter."""
    
    def _split(self, html: str):
        urls = parse_image_urls(html)
        print(f"Parsed {len(urls)} image URLs")
        return tuple(urls)

# ========== Build Task Graph ==========

def build_crawler_graph(keyword: str) -> TaskGraph:
    """Build the crawler task graph."""
    
    # Create nodes
    stage_search = TaskStage(
        func=search_images,
        execution_mode="serial",
        max_retries=2,
    )
    
    stage_parse = URLSplitter()
    
    stage_download = TaskStage(
        func=download_image,
        execution_mode="thread",
        worker_limit=10,
        max_retries=3,
    )
    
    # Use closure to pass keyword
    stage_save = TaskStage(
        func=lambda data: save_image(data, keyword),
        execution_mode="serial",
        enable_duplicate_check=False,
    )
    
    # Set up connections
    graph = TaskGraph(schedule_mode="eager", log_level="SUCCESS")
    graph.set_stages(root_stages=[stage_search], stages=[stage_parse, stage_download, stage_save])
    graph.connect([stage_search], [stage_parse])
    graph.connect([stage_parse], [stage_download])
    graph.connect([stage_download], [stage_save])
    
    return graph

# ========== Main Program ==========

if __name__ == "__main__":
    # Configuration
    KEYWORDS = ["猫咪", "小狗", "风景"]
    
    # Build graph
    graph = build_crawler_graph(KEYWORDS[0])
    graph.set_reporter(True, host="127.0.0.1", port=5005)
    
    # Run
    print("Starting image crawl...")
    graph.start_graph({
        graph.root_stages[0].get_tag(): KEYWORDS
    })
    
    # Statistics
    summary = graph.get_graph_summary()
    print(f"\nCrawl complete!")
    print(f"Succeeded: {summary.get('total_successed', 0)}")
    print(f"Failed: {summary.get('total_failed', 0)}")
```

---

## Step 5: Run and Debug

### 5.1 Start the Web Service

```bash
# Terminal 1: Start the Web service
celestialflow-web --port 5005
```

### 5.2 Run the Crawler

```bash
# Terminal 2: Run the crawler
python crawler.py
```

### 5.3 View the Web UI

Open http://localhost:5005, where you can see:

1. **Dashboard**: Real-time display of processing progress for each node
2. **Structure**: Visualization of the task graph structure
3. **Errors**: Failed image URLs and error messages
4. **Task Injection**: Dynamically inject new keywords

### 5.4 View Results

```bash
# View downloaded images
ls images/猫咪/
ls images/小狗/
ls images/风景/
```

---

## Extension: Dynamic Task Injection

You can dynamically inject new keywords through the Web UI:

```python
# Or inject via code
from celestialflow import TerminationSignal

# Inject new keywords
graph.put_stage_queue({
    stage_search.get_tag(): ["汽车", "美食"]
})

# Inject termination signal (stop crawling)
graph.put_stage_queue({
    stage_search.get_tag(): [TerminationSignal()]
})
```

---

## Summary

This tutorial demonstrated the complete CelestialFlow workflow:

1. **Task Analysis**: Break down complex tasks into independent layers
2. **Function Writing**: Write processing functions for each layer and test them individually
3. **Node Creation**: Wrap functions as `TaskStage` instances
4. **Graph Assembly**: Organize node relationships with `TaskGraph`
5. **Monitored Execution**: Monitor execution status in real time through the Web UI

### Key Concepts Review

| Concept | Description |
|---------|-------------|
| `TaskStage` | Task node that wraps a processing function |
| `TaskSplitter` | Splitter that divides one task into multiple tasks |
| `TaskGraph` | Task graph that organizes node relationships and execution flow |
| `stage_mode` | Node execution mode (serial/process) |
| `execution_mode` | Internal execution mode within a node (serial/thread) |

### Next Steps

- Try using `TaskRouter` for conditional routing
- Explore `TaskRedisTransport` for cross-language collaboration
- Read other [API References](reference/stage/core_executor.md) for more features
