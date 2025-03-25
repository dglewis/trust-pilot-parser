import json
import argparse
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Configuration parameters
CONFIG = {
    # Input/Output
    'default_input_file': 'complete_reviews.json',
    'default_output_file': 'review_analysis.png',
    
    # Graph settings
    'figure_size': (15, 10),
    'dpi': 300,
    'y_axis_limit': 5.2,
    'legend_position': (1.15, 1),
    'legend_fontsize': 10
}

def generate_graph(input_file=None, output_file=None):
    """Generate review analysis graphs from JSON data"""
    # Use defaults if not specified
    input_file = input_file or CONFIG['default_input_file']
    output_file = output_file or CONFIG['default_output_file']
    
    # Set the style for better aesthetics
    plt.style.use('seaborn-v0_8')  # Updated style name for compatibility
    sns.set(style="whitegrid")  # Use seaborn's set function instead

    # Load JSON data from file
    with open(input_file, 'r') as f:
        data = json.load(f)

    reviews = data['reviews']

    # Process reviews: group by year and month
    monthly_data = defaultdict(lambda: {'ratings': [], 'counts': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}})
    for review in reviews:
        date_str = review['date']['published']
        rating = review['stars']
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        year, month = dt.year, dt.month
        monthly_data[(year, month)]['ratings'].append(rating)
        monthly_data[(year, month)]['counts'][rating] += 1

    # Sort months chronologically
    sorted_months = sorted(monthly_data.keys())

    # Prepare data for plotting
    labels = [f"{year}-{month:02d}" for year, month in sorted_months]
    averages = [sum(monthly_data[(year, month)]['ratings']) / len(monthly_data[(year, month)]['ratings']) 
                for year, month in sorted_months]
    one_star = [monthly_data[(year, month)]['counts'][1] for year, month in sorted_months]
    two_star = [monthly_data[(year, month)]['counts'][2] for year, month in sorted_months]
    three_star = [monthly_data[(year, month)]['counts'][3] for year, month in sorted_months]
    four_star = [monthly_data[(year, month)]['counts'][4] for year, month in sorted_months]
    five_star = [monthly_data[(year, month)]['counts'][5] for year, month in sorted_months]

    # Create figure with subplots
    fig = plt.figure(figsize=CONFIG['figure_size'])
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1])

    # Plot 1: Average Rating Over Time
    ax1 = fig.add_subplot(gs[0])
    line = ax1.plot(labels, averages, marker='o', linewidth=2, markersize=8)
    color = line[0].get_color()  # Get the color from the line
    ax1.fill_between(labels, averages, alpha=0.2, color=color)
    ax1.set_xlabel('Month', fontsize=12, fontweight='bold', labelpad=10)
    ax1.set_ylabel('Average Rating', fontsize=12, fontweight='bold', labelpad=10)
    ax1.set_title('Average Rating Trend Over Time', fontsize=14, fontweight='bold', pad=20)
    ax1.tick_params(axis='x', rotation=45, labelsize=10)
    ax1.tick_params(axis='y', labelsize=10)
    ax1.grid(True, linestyle='--', alpha=0.3)
    ax1.set_ylim(0, CONFIG['y_axis_limit'])

    # Add horizontal lines for reference
    for rating in range(1, 6):
        ax1.axhline(y=rating, color='gray', linestyle='--', alpha=0.2)

    # Plot 2: Rating Distribution Over Time
    ax2 = fig.add_subplot(gs[1])
    bottom = np.zeros(len(labels))

    # Use color palette from seaborn
    colors = sns.color_palette("viridis", 5)
    colors.reverse()  # Reverse for better visualization (5-star at bottom)
    labels_rating = ['1-star', '2-star', '3-star', '4-star', '5-star']
    ratings_data = [one_star, two_star, three_star, four_star, five_star]

    for rating_data, color, label in zip(ratings_data, colors, labels_rating):
        ax2.bar(labels, rating_data, bottom=bottom, label=label, color=color, alpha=0.8)
        bottom += rating_data

    ax2.set_xlabel('Month', fontsize=12, fontweight='bold', labelpad=10)
    ax2.set_ylabel('Number of Reviews', fontsize=12, fontweight='bold', labelpad=10)
    ax2.set_title('Rating Distribution Over Time', fontsize=14, fontweight='bold', pad=20)
    ax2.tick_params(axis='x', rotation=45, labelsize=10)
    ax2.tick_params(axis='y', labelsize=10)
    ax2.grid(True, linestyle='--', alpha=0.3)
    ax2.legend(loc='upper right', bbox_to_anchor=CONFIG['legend_position'], fontsize=CONFIG['legend_fontsize'])

    # Add total reviews count as text on top of bars
    for i, total in enumerate(bottom):
        if total > 0:  # Only add text if there are reviews
            ax2.text(i, total + 1, f"{int(total)}", ha='center', va='bottom', fontsize=8)

    # Adjust layout and display
    plt.tight_layout()
    plt.show()

    # Save the figure
    plt.savefig(output_file, dpi=CONFIG['dpi'], bbox_inches='tight')
    print(f"Graph saved to {output_file}")

def parse_args():
    parser = argparse.ArgumentParser(description='Generate graphs from Trustpilot review data')
    parser.add_argument('-i', '--input', help=f'Input JSON file (default: {CONFIG["default_input_file"]})')
    parser.add_argument('-o', '--output', help=f'Output image file (default: {CONFIG["default_output_file"]})')
    return parser.parse_args()

def main():
    args = parse_args()
    generate_graph(args.input, args.output)

if __name__ == "__main__":
    main()