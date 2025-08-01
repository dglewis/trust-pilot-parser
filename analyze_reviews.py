import json
import argparse
import re
from collections import Counter
from textblob import TextBlob

# Common words to exclude from theme analysis
STOP_WORDS = [
    'a', 'an', 'and', 'the', 'in', 'is', 'it', 'of', 'to', 'for', 'on', 'with',
    'i', 'me', 'my', 'myself', 'we', 'our', 'ourselves', 'you', 'your',
    'yours', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
    'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
    'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but',
    'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for',
    'with', 'about', 'against', 'between', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in',
    'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
    'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't',
    'can', 'will', 'just', 'don', 'should', 'now', 'dea', 'academy', 'course', 'data', 'learning'
]

def analyze_sentiment(text):
    """
    Analyzes the sentiment of a given text.
    Returns a sentiment polarity score (-1 to 1).
    """
    if not text:
        return 0
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def find_common_themes(reviews, num_themes=10):
    """
    Finds common themes in a list of reviews.
    Returns a list of the most common words.
    """
    all_text = ' '.join([review['text'] for review in reviews])
    words = re.findall(r'\b\w+\b', all_text.lower())
    
    # Filter out stop words
    filtered_words = [word for word in words if word not in STOP_WORDS and not word.isdigit()]
    
    word_counts = Counter(filtered_words)
    return word_counts.most_common(num_themes)

def generate_report(analysis_results, output_file):
    """Generates a Markdown report of the analysis."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Trustpilot Review Analysis\n\n")
        
        # Summary
        f.write("## Review Analysis by Star Rating\n")
        f.write(f"- **Total Reviews Analyzed:** {analysis_results['total_reviews']}\n")
        f.write(f"- **5-Star Reviews:** {len(analysis_results['5_star'])}\n")
        f.write(f"- **4-Star Reviews:** {len(analysis_results['4_star'])}\n")
        f.write(f"- **3-Star Reviews:** {len(analysis_results['3_star'])}\n")
        f.write(f"- **2-Star Reviews:** {len(analysis_results['2_star'])}\n")
        f.write(f"- **1-Star Reviews:** {len(analysis_results['1_star'])}\n\n")

        # Positive Themes
        if analysis_results['positive_themes']:
            f.write("## Common Themes in Positive (4-5 Star) Reviews\n")
            for theme, count in analysis_results['positive_themes']:
                f.write(f"- **{theme}:** {count} mentions\n")
            f.write("\n")

        # Negative Themes
        if analysis_results['negative_themes']:
            f.write("## Common Themes in Negative (1-2 Star) Reviews\n")
            for theme, count in analysis_results['negative_themes']:
                f.write(f"- **{theme}:** {count} mentions\n")
            f.write("\n")
        
        # Full Negative Reviews
        if analysis_results['low_star_reviews']:
            f.write("## Full Text of Negative (1-2 Star) Reviews\n")
            for i, review in enumerate(analysis_results['low_star_reviews'], 1):
                f.write(f"\n### Review #{i}\n")
                f.write(f"- **Stars:** {review['stars']}\n")
                f.write(f"- **Sentiment Score:** {review['sentiment']:.2f}\n")
                f.write(f"- **Text:** {review['text']}\n")
                f.write("\n---\n")

def main():
    """Main function to analyze reviews."""
    parser = argparse.ArgumentParser(description='Analyze sentiment of Trustpilot reviews.')
    parser.add_argument('-i', '--input', required=True, help='Input JSON file with reviews')
    parser.add_argument('-o', '--output', help='Output Markdown report file')
    args = parser.parse_args()

    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at {args.input}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {args.input}")
        return

    reviews = data.get('reviews', [])
    if not reviews:
        print("No reviews found in the input file.")
        return

    all_reviews_data = []
    for review in reviews:
        text_to_analyze = f"{review.get('title', '')}. {review.get('text', '')}"
        sentiment = analyze_sentiment(text_to_analyze)
        all_reviews_data.append({
            'stars': review.get('stars'),
            'text': text_to_analyze,
            'sentiment': sentiment
        })

    one_star_reviews = [r for r in all_reviews_data if r['stars'] == 1]
    two_star_reviews = [r for r in all_reviews_data if r['stars'] == 2]
    three_star_reviews = [r for r in all_reviews_data if r['stars'] == 3]
    four_star_reviews = [r for r in all_reviews_data if r['stars'] == 4]
    five_star_reviews = [r for r in all_reviews_data if r['stars'] == 5]
    
    low_star_reviews = one_star_reviews + two_star_reviews
    high_star_reviews = four_star_reviews + five_star_reviews

    analysis_results = {
        'total_reviews': len(reviews),
        '5_star': five_star_reviews,
        '4_star': four_star_reviews,
        '3_star': three_star_reviews,
        '2_star': two_star_reviews,
        '1_star': one_star_reviews,
        'low_star_reviews': low_star_reviews,
        'positive_themes': find_common_themes(high_star_reviews) if high_star_reviews else [],
        'negative_themes': find_common_themes(low_star_reviews) if low_star_reviews else [],
    }

    if args.output:
        generate_report(analysis_results, args.output)
        print(f"Analysis report saved to {args.output}")
    else:
        # Print to console if no output file is specified
        print(f"--- REVIEW ANALYSIS BY STAR RATING ---")
        print(f"Total reviews analyzed: {len(reviews)}")
        print(f"5-Star Reviews: {len(five_star_reviews)}")
        print(f"4-Star Reviews: {len(four_star_reviews)}")
        print(f"3-Star Reviews: {len(three_star_reviews)}")
        print(f"2-Star Reviews: {len(two_star_reviews)}")
        print(f"1-Star Reviews: {len(one_star_reviews)}\n")


        if high_star_reviews:
            print("--- COMMON THEMES IN POSITIVE (4-5 STAR) REVIEWS ---")
            for theme, count in analysis_results['positive_themes']:
                print(f"- {theme}: {count} mentions")
        
        if low_star_reviews:
            print("\n--- COMMON THEMES IN NEGATIVE (1-2 STAR) REVIEWS ---")
            if analysis_results['negative_themes']:
                for theme, count in analysis_results['negative_themes']:
                    print(f"- {theme}: {count} mentions")
            else:
                print("No significant common themes found in negative reviews.")

            print("\n--- FULL TEXT OF NEGATIVE (1-2 STAR) REVIEWS ---")
            for i, review in enumerate(low_star_reviews, 1):
                print(f"\nReview #{i}:")
                print(f"  Stars: {review['stars']}")
                print(f"  Sentiment Score: {review['sentiment']:.2f}")
                print(f"  Text: {review['text']}")

if __name__ == '__main__':
    main()
