# Trustpilot Review Scraper

A tool for extracting reviews from Trustpilot, particularly useful for collecting data for analysis.

## Requirements

- Python 3.6+
- Chrome or Chromium browser (for headless web scraping)
- Dependencies listed in requirements.txt or pyproject.toml

## Installation

### Using uv (recommended)

```bash
# Initialize the project
uv init

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

Basic usage:

```bash
python trustpilot_scraper.py "https://www.trustpilot.com/review/your-company.com"
```

#### Command-line Options

- `-o, --output`: Specify the output file path (default: `trustpilot_reviews.json`)
- `-f, --format`: Choose the output format: `json` or `csv` (default: `json`)
- `-s, --stars`: Filter by star ratings (e.g., `-s 1 4 5` for 1, 4, and 5-star reviews)
- `-p, --max-pages`: Maximum number of pages to scrape (default: all available pages)
- `--pretty`: Pretty print JSON output (enabled by default)

#### Examples

Extract all reviews and save as JSON:
```bash
python trustpilot_scraper.py "https://www.trustpilot.com/review/dataengineeracademy.com"
```

Extract only 1-star and 5-star reviews and save as CSV:
```bash
python trustpilot_scraper.py "https://www.trustpilot.com/review/dataengineeracademy.com" -s 1 5 -f csv -o "filtered_reviews.csv"
```

Extract reviews from the first 3 pages only:
```bash
python trustpilot_scraper.py "https://www.trustpilot.com/review/dataengineeracademy.com" -p 3
```

### Data Visualization

After extracting reviews to a JSON file, you can generate visualizations using the `gen_graph.py` script:

```bash
python gen_graph.py -i your_reviews.json -o output_graph.png
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

## Future Enhancements

See the [todo.md](todo.md) file for planned future enhancements.
