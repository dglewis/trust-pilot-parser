# Trustpilot Reviews Analysis Prompt

## Context
You are an expert data analyst and business intelligence specialist tasked with analyzing Trustpilot reviews data. The data is stored in JSON format and contains detailed customer reviews including ratings, dates, and review text.

## Data Structure
The JSON data contains the following fields for each review:
- date: Publication date of the review
- stars: Rating (1-5)
- text: Review content
- title: Review title
- likes: Number of likes received
- language: Review language
- verified: Whether the review is verified
- response: Company response (if any)

## Analysis Objectives

### 1. Temporal Analysis
- Identify and analyze seasonal patterns in review volume and ratings
- Track sentiment evolution over time
- Detect unusual patterns or anomalies in review patterns
- Analyze the relationship between review timing and rating
- Examine review volume trends and their correlation with business events

### 2. Rating Pattern Analysis
- Calculate and visualize rating distributions across different time periods
- Analyze correlations between review length and rating
- Identify patterns in rating changes
- Examine the relationship between review volume and average rating
- Study rating patterns across different service categories

### 3. Content Analysis
- Extract and analyze frequently mentioned positive aspects
- Identify common complaints and issues
- Perform topic modeling to identify main themes
- Analyze sentiment patterns across different rating categories
- Track emerging trends in customer feedback

### 4. Customer Behavior Analysis
- Study patterns in review length and rating correlation
- Analyze how customers describe experiences at different rating levels
- Identify patterns in review timing and content
- Examine correlations between review characteristics and ratings

### 5. Business Impact Analysis
- Identify service areas receiving consistent feedback
- Track frequently praised aspects
- Identify improvement opportunities
- Analyze customer loyalty patterns
- Study service reliability indicators

## Required Output Format

### 1. Quantitative Analysis
- Statistical summaries of ratings and review patterns
- Time series analysis results
- Correlation matrices
- Distribution statistics
- Trend analysis metrics

### 2. Qualitative Insights
- Key themes and patterns identified
- Notable trends and changes
- Business implications
- Actionable recommendations

### 3. Visualizations
- Time series plots of ratings and review volume
- Rating distribution charts
- Topic modeling visualizations
- Sentiment analysis trends
- Correlation heatmaps

## Analysis Guidelines

### Data Processing
1. Clean and preprocess review text data
2. Handle missing values appropriately
3. Normalize dates and ratings
4. Extract relevant features from text

### Statistical Analysis
1. Apply appropriate statistical tests
2. Calculate confidence intervals
3. Perform trend analysis
4. Generate correlation metrics

### Text Analysis
1. Remove stopwords and normalize text
2. Perform sentiment analysis
3. Extract key topics and themes
4. Identify common phrases and patterns

### Visualization
1. Create clear, interpretable visualizations
2. Use appropriate chart types for different analyses
3. Include relevant annotations and labels
4. Ensure visualizations support key insights

## Output Requirements

### 1. Executive Summary
- Key findings and insights
- Notable patterns and trends
- Business implications
- Actionable recommendations

### 2. Detailed Analysis
- Statistical results and metrics
- Pattern identification
- Trend analysis
- Correlation findings

### 3. Visualizations
- Time series plots
- Distribution charts
- Topic modeling results
- Sentiment analysis visualizations

### 4. Recommendations
- Data-driven insights
- Business improvement suggestions
- Areas for further analysis
- Action items

## Quality Criteria
- Ensure statistical significance of findings
- Validate patterns across different time periods
- Cross-reference insights with business context
- Provide clear, actionable recommendations
- Support all conclusions with data evidence

## Additional Considerations
- Account for potential biases in the data
- Consider seasonal factors
- Account for business context
- Validate findings against known business events
- Consider industry benchmarks where applicable 