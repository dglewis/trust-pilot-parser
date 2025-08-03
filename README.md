# Trustpilot Review Scraper

A tool for extracting reviews from Trustpilot, particularly useful for collecting data for analysis.

## Requirements

- Python 3.12+
- Chrome or Chromium browser (for headless web scraping)

## Installation

### Using uv (recommended)

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### Alternative: Using standard pip

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Review Extraction

The recommended way to run the scripts is by using `uv run`, which executes commands within the project's virtual environment without needing to activate it first.

Basic usage:

```bash
uv run python trustpilot_scraper.py "https://www.trustpilot.com/review/some-company.com"
```

Alternatively, if you have activated the virtual environment (`source .venv/bin/activate`), you can use `python` directly:

```bash
python trustpilot_scraper.py "https://www.trustpilot.com/review/some-company.com"
```

All examples below use the recommended `uv run` method.

#### Command-line Options

- `-o, --output`: Specify the output file path (default: `trustpilot_reviews.json`)
- `-f, --format`: Choose the output format: `json` or `csv` (default: `json`)
- `-s, --stars`: Filter by star ratings (e.g., `-s 1 4 5` for 1, 4, and 5-star reviews)
- `-p, --max-pages`: Maximum number of pages to scrape (default: all available pages)
- `--pretty`: Pretty print JSON output (enabled by default)
- `--debug`: Enable debug mode with verbose output and HTML saving
- `--debug-html-path`: Path to save debug HTML (default: debug_page.html)

#### Performance Options

- `--page-load-timeout`: Timeout for page loading in seconds (default: 15)
- `--retry-delay`: Delay between retries in seconds (default: 2)
- `--page-delay`: Delay between pages in seconds (default: 2)
- `--max-retries`: Maximum number of retries per page (default: 3)

#### Examples

Extract all reviews and save as JSON:
```bash
uv run python trustpilot_scraper.py "https://www.trustpilot.com/review/dataengineeracademy.com"
```

Extract only 1-star and 5-star reviews and save as CSV:
```bash
uv run python trustpilot_scraper.py "https://www.trustpilot.com/review/dataengineeracademy.com" -s 1 5 -f csv -o "filtered_reviews.csv"
```

Extract reviews from the first 3 pages only:
```bash
uv run python trustpilot_scraper.py "https://www.trustpilot.com/review/dataengineeracademy.com" -p 3
```

Enable debug mode for troubleshooting:
```bash
uv run python trustpilot_scraper.py "https://www.trustpilot.com/review/dataengineeracademy.com" --debug
```

### Intelligent Review Analysis and Reporting

After extracting reviews, you can use the `analyze_reviews.py` script to perform a comprehensive, AI-powered analysis. This script goes beyond simple sentiment scores by leveraging a local Large Language Model (LLM) via Ollama to generate a nuanced, human-like summary of the findings.

#### Generating an Intelligent Analysis Report

To generate a full analysis report in Markdown format, you must specify both an input and an output file.

```bash
uv run python analyze_reviews.py -i output/tp_dea_reviews.json -o output/analysis_report.md
```

The report provides a multi-faceted view of the customer feedback, including:
- An **AI-Generated Summary** offering a high-level, interpretive overview of the key findings.
- A **Detailed Quantitative Analysis** of the review distribution.
- **Key Themes from Positive and Negative Reviews**, identified using topic modeling, complete with representative example reviews for each theme.
- The **Full Text of all 1- and 2-star reviews** for detailed manual inspection.

#### Viewing Analysis in the Console

If you prefer to see the analysis directly in your terminal, simply omit the `-o` flag:
```bash
uv run python analyze_reviews.py -i tp_dea_reviews.json
```

### Data Visualization

After extracting reviews to a JSON file, you can generate visualizations using the `gen_graph.py` script:

```bash
uv run python gen_graph.py -i your_reviews.json -o output_graph.png
```

#### Command-line Options

- `-i, --input`: Specify the input JSON file (default: `complete_reviews.json`)
- `-o, --output`: Specify the output image file path (default: `review_analysis.png`)

The generated visualization includes:
1. Average rating trend over time
2. Rating distribution breakdown by month

## Output Format

### JSON Structure

The JSON output contains a rich structure with detailed information:

```json
{
  "metadata": {
    "total_reviews": 141,
    "extracted_date": "2023-07-29T18:45:30",
    "version": "2.0"
  },
  "reviews": [
    {
      "stars": 5,
      "title": "Definitely Recommend",
      "text": "Chris and the team at DE Academy are amazing...",
      "company_response": "Thank you for your feedback!",
      "reviewer": {
        "name": "John Doe",
        "location": "United States",
        "reviews_count": 3
      },
      "date": {
        "published": "2023-06-15T10:23:45Z",
        "experience": "June 2023"
      },
      "metadata": {
        "verified": true,
        "useful_votes": 5,
        "page_number": 1,
        "source_url": "https://www.trustpilot.com/review/dataengineeracademy.com",
        "company_reply_name": "Data Engineer Academy"
      }
    }
  ]
}
```

### CSV Format

The CSV output flattens the nested structure for easier spreadsheet analysis, with columns including:

- `stars`: Rating (1-5)
- `title`: Review title
- `text`: Main review content
- `company_response`: Response from the company
- `reviewer_name`: Name of reviewer
- `reviewer_location`: Location of reviewer
- `reviewer_reviews_count`: Number of reviews by this reviewer
- `date_published`: When the review was published
- `date_experience`: When the experience occurred
- `verified`: Whether the review is verified
- `useful_votes`: Number of helpful/useful votes
- `page_number`: Page where the review was found

## Configuration

Both tools support configuration through their respective files:

- `trustpilot_scraper.py`: Contains a `CONFIG` dictionary at the top of the file for adjusting browser settings, timeouts, and more
- `gen_graph.py`: Contains a `CONFIG` dictionary for customizing graph appearance and file paths

## Notes

- The script uses Selenium with a headless Chrome browser to handle JavaScript-rendered content
- Pagination is automatically handled to extract all reviews
- The script respects website constraints by adding appropriate delays between requests
- Debug mode is off by default for cleaner output; enable with `--debug` when troubleshooting

## Future Enhancements

See the [todo.md](todo.md) file for planned future enhancements.
