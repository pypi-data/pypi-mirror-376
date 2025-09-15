[![PyPI Downloads](https://static.pepy.tech/personalized-badge/ljobx?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/ljobx)

# LinkedIn Job Extractor (ljobx)

A fast, simple **command-line tool** to scrape LinkedIn job postings without needing to log in. It uses LinkedIn’s public APIs, supports flexible proxy configurations, and saves results to JSON or CSV.

-----

### ✨ Features

* **No Login Needed**: Scrapes public job postings anonymously.
* **Advanced Filtering**: Filter by date, experience level, job type, and remote options.
* **Concurrent Scraping**: Fetches multiple jobs at once with randomized delays.
* **Flexible Proxy Support**: Load proxies from API providers (like Webshare) or directly from your own local text files.
* **Structured Output**: Save results as clean, timestamped `JSON` or `CSV` files.
* **Latest Symlink**: Automatically creates a `_latest` file pointing to the newest results.

-----

### 📥 Installation

```sh
pip install ljobx
```

-----

### 🚀 Usage

Provide a search query and a location. Use flags for more control.

```sh
# Basic search saving to CSV
ljobx "Software Engineer" "Remote" --to-csv

# Advanced search with multiple filters
ljobx "Senior Python Developer" "Noida, India" \
      --job-type "Full-time" \
      --date-posted "Past week" \
      --max-jobs 50 \
      --concurrency 2
      --delay 3 8
```

-----

### ⚙️ CLI Options

**Required Arguments:**

* `keywords`: The job title or skill to search for.
* `location`: The geographical location (e.g., "Noida, India", "Remote").

**Filtering Options:**

* `--date-posted`: `Any time`, `Past month`, `Past week`, `Past 24 hours`
* `--experience-level`: `Internship`, `Entry level`, `Associate`, `Mid-Senior level`, etc.
* `--job-type`: `Full-time`, `Contract`, `Part-time`, etc.
* `--remote`: `On-site`, `Remote`, `Hybrid`

**Scraper Settings:**

* `--max-jobs`: Max number of jobs to scrape (Default: `25`).
* `--concurrency`: Number of parallel requests (Default: `2`).
* `--delay MIN MAX`: Random delay range in seconds (Default: `3 8`).
* `--to-csv`: Save output as a CSV file instead of JSON.
* `--proxy-config FILE_OR_URL`: Path or URL to a proxy YAML config.

> 💡 **A Note on Performance**: It's highly recommended to adjust `--concurrency` and `--delay` based on your proxy setup.
>
>   * **With many working proxies**, you can be more aggressive for faster scraping (e.g., `--concurrency 10 --delay 1 3`).
>   * **With few or no proxies**, you must be conservative to avoid getting blocked. **It's safest to use the default values.**

-----

### 🔌 Proxy Configuration

The tool offers a powerful and flexible proxy system configured via a YAML file. You can load proxies from supported API providers and your own local text files simultaneously.

**Example `config.yml`:**

```yaml
# --- API Providers (Optional) ---
# Fetches proxies from a supported provider's API.
proxy_providers:
  - name: webshare
    config:
      api_key: "YOUR_WEBSHARE_API_KEY"

# --- Local Files (Optional) ---
# Loads proxies directly from your own text files.
proxies_files:
  # Option 1: Provide a default protocol.
  # The program will add "socks5://" to any proxy in this file that doesn't have one.
  # It will also skip any proxies that have a different protocol (e.g., https://).
  - path: "/path/to/your/socks_proxies.txt"
    protocol: "socks5"

  # Option 2: No default protocol.
  # Every proxy in this file must be a complete URL (e.g., "https://user:pass@ip:port").
  # Incomplete proxies will be skipped.
  - path: "/path/to/your/mixed_proxies.txt"

# Optional: Set to true to test proxies before scraping.
# Avoid setting this to true if you have many proxies.
validate_proxies: false 
```

#### Loading Proxies from Files (`proxies_files`)

This feature gives you full control over your proxy lists. The system follows these rules:

* **Default Protocol:** If you specify a `protocol` (e.g., `"socks5"` or `"https"`), it will be automatically added to any proxy in that file that doesn't already have one. It will also enforce that protocol, skipping any proxies in the file that have a different prefix.
* **No Default Protocol:** If you only provide the `path`, the tool expects every line in the file to be a complete proxy URL (e.g., `socks5://user:pass@ip:port`). Incomplete proxies will be skipped.
* **Security Filter:** For your safety, the tool will **always** ignore any proxy that starts with insecure `http://`.

**Command:**

```sh
ljobx "Java Developer" "Delhi, India" --proxy-config "config.yml"
```

-----

### 📂 Output & Data Fields

Results are saved as timestamped `JSON` or `CSV` files (e.g., `keywords_YYYYMMDD_HHMMSS.json`), with a `_latest` symlink for easy access.

The scraper extracts the following data for each job:

* `job_id`
* `title`
* `company`
* `location`
* `posted_date`
* `applicants` (if available)
* `salary_range` (if available)
* `description`
* `apply` (URL and whether it's an "Easy Apply")
* `recruiter` (Name, Title, and Profile URL, if available)