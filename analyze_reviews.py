import json
import argparse
import re
from collections import Counter
from textblob import TextBlob
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import numpy as np
import requests
import nltk

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

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

def generate_llm_summary(analysis_results):
    """Generates a human-like summary using a local LLM via Ollama."""
    prompt = f"""
    You are a professional data analyst. Based on the following Trustpilot review analysis, provide a concise, human-like summary.
    Your summary should include:
    1. A brief overview of the sentiment distribution.
    2. Key insights from the positive reviews, referencing the discovered topics.
    3. Key insights from the negative reviews, referencing the discovered topics and specific issues raised.
    4. A concluding paragraph that synthesizes the findings and offers a balanced perspective.

    **Analysis Data:**
    - Total Reviews: {analysis_results['total_reviews']}
    - Positive (4-5 Star) Reviews Percentage: {analysis_results['positive_percentage']:.1f}%
    
    **Positive Review Topics:**
    {analysis_results['positive_topics']}

    **Negative Review Topics:**
    {analysis_results['negative_topics']}

    **Full text of negative reviews:**
    {analysis_results['low_star_reviews']}
    """

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama3.2:latest',
                'prompt': prompt,
                'stream': False
            }
        )
        response.raise_for_status()
        return response.json().get('response', "Error: Could not get a valid response from the LLM.")
    except requests.exceptions.RequestException as e:
        return f"Error: Could not connect to the Ollama server. Please ensure Ollama is running. Details: {e}"


def lemmatize_text(text):
    lemmatizer = WordNetLemmatizer()
    return ' '.join([lemmatizer.lemmatize(word) for word in word_tokenize(text.lower()) if word.isalpha() and word not in STOP_WORDS])

def perform_topic_modeling(reviews, num_topics=3, num_words=5):
    """Performs topic modeling and finds representative reviews."""
    if not reviews or len(reviews) < num_topics:
        return []

    docs = [lemmatize_text(review['text']) for review in reviews]
    
    if not any(docs):
        return []

    vectorizer = CountVectorizer(stop_words='english', max_df=0.9, min_df=2)
    try:
        X = vectorizer.fit_transform(docs)
    except ValueError:
        return []

    if X.shape[0] == 0:
        return []

    lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
    doc_topic_dist = lda.fit_transform(X)

    topics = []
    feature_names = vectorizer.get_feature_names_out()
    for topic_idx, topic_dist in enumerate(lda.components_):
        top_words = [feature_names[i] for i in topic_dist.argsort()[:-num_words - 1:-1]]
        
        # Find the most representative review for this topic
        representative_doc_index = np.argmax(doc_topic_dist[:, topic_idx])
        representative_review = reviews[representative_doc_index]['text']
        
        topics.append({
            'topic_num': topic_idx + 1,
            'keywords': ', '.join(top_words),
            'representative_review': representative_review
        })
    
    return topics

def analyze_sentiment(text):
    """
    Analyzes the sentiment of a given text.
    Returns a sentiment polarity score (-1 to 1).
    """
    if not text:
        return 0
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def generate_report(analysis_results, llm_summary, output_file):
    """Generates a Markdown report of the analysis."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Trustpilot Review Analysis\n\n")
        
        f.write("## AI-Generated Summary\n\n")
        f.write(f"{llm_summary}\n\n")
        
        f.write("---\n")
        f.write("## Detailed Analysis\n\n")
        f.write(f"This report analyzes **{analysis_results['total_reviews']}** reviews. The sentiment is overwhelmingly positive, with **{analysis_results['positive_percentage']:.1f}%** of reviews being 4 or 5 stars. However, a small but significant number of 1-star reviews highlight specific areas for improvement.\n\n")

        # Topic Modeling
        if analysis_results['positive_topics']:
            f.write("### Key Themes from Positive Reviews\n")
            for topic in analysis_results['positive_topics']:
                f.write(f"**Topic {topic['topic_num']}:** {topic['keywords']}\n")
                f.write(f"> **Representative Review:** \"*{topic['representative_review'].strip()}*\"\n\n")

        if analysis_results['negative_topics']:
            f.write("### Key Themes from Negative Reviews\n")
            for topic in analysis_results['negative_topics']:
                f.write(f"**Topic {topic['topic_num']}:** {topic['keywords']}\n")
                f.write(f"> **Representative Review:** \"*{topic['representative_review'].strip()}*\"\n\n")

        f.write("---\n")
        f.write("### Full Text of Negative (1-2 Star) Reviews\n")
        if analysis_results['low_star_reviews']:
            for i, review in enumerate(analysis_results['low_star_reviews'], 1):
                f.write(f"\n**Review #{i} (Stars: {review['stars']})**\n")
                f.write(f"**Sentiment Score:** {review['sentiment']:.2f}\n\n")
                f.write(f"{review['text']}\n\n")


def main():
    """Main function to analyze reviews."""
    parser = argparse.ArgumentParser(description='Analyze sentiment of Trustpilot reviews.')
    parser.add_argument('-i', '--input', required=True, help='Input JSON file with reviews')
    parser.add_argument('-o', '--output', required=True, help='Output Markdown report file')
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
    
    positive_percentage = (len(high_star_reviews) / len(reviews)) * 100 if reviews else 0

    analysis_results = {
        'total_reviews': len(reviews),
        'positive_percentage': positive_percentage,
        'low_star_reviews': low_star_reviews,
        'positive_topics': perform_topic_modeling(high_star_reviews),
        'negative_topics': perform_topic_modeling(low_star_reviews),
    }

    print("Generating AI summary with local LLM...")
    llm_summary = generate_llm_summary(analysis_results)
    
    generate_report(analysis_results, llm_summary, args.output)
    print(f"Intelligent analysis report with AI summary saved to {args.output}")


if __name__ == '__main__':
    main()
