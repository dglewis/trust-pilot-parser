# Trustpilot Reviews Analysis System Design

## System Overview

This design document outlines an extension to the existing Trustpilot review processing system. The design respects and builds upon the current codebase structure, which consists of a scraper (`trustpilot_scraper.py`) and a visualization component (`gen_graph.py`).

## Current System Architecture

The existing system follows this workflow:
1. `trustpilot_scraper.py` extracts reviews from Trustpilot and stores them in JSON format
2. `gen_graph.py` loads the JSON data and generates visualization graphs showing rating trends

## Design Principles

1. **Respect Existing Code**: Maintain compatibility with current scraper and visualization components
2. **Modular Extension**: Add analysis capabilities without modifying core functionality
3. **Minimal Dependencies**: Introduce new dependencies only when necessary
4. **Python 3.12 Compatibility**: Ensure all components work with Python 3.12 as specified in the project

## Extended System Architecture

```
┌───────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│                   │     │                    │     │                    │
│  Data Acquisition │────▶│  Data Processing   │────▶│  Analysis Engine   │
│  (trustpilot_     │     │  (Extended from    │     │  (New Component)   │
│   scraper.py)     │     │   gen_graph.py)    │     │                    │
└───────────────────┘     └────────────────────┘     └────────────────────┘
                                                             │
                                                             ▼
                           ┌────────────────────┐     ┌────────────────────┐
                           │                    │     │                    │
                           │  Visualization     │◀────│  Insight Generator │
                           │  (Enhanced         │     │  (New Component)   │
                           │   gen_graph.py)    │     │                    │
                           └────────────────────┘     └────────────────────┘
```

### Components Description

#### 1. Data Acquisition (Existing)
- Uses `trustpilot_scraper.py` to extract review data
- No modifications required to this component

#### 2. Data Processing (Extended)
- Builds on existing JSON loading in `gen_graph.py`
- Adds text preprocessing capabilities
- Implements feature extraction for advanced analysis

#### 3. Analysis Engine (New)
- Implements multiple analysis modules:
  - Temporal Analysis: Time-based patterns and trends
  - Content Analysis: Text-based insights and topic modeling
  - Rating Pattern Analysis: Statistical analysis of ratings
  - Customer Behavior Analysis: Behavioral patterns and correlations

#### 4. Insight Generator (New)
- Processes analysis results to generate actionable insights
- Identifies patterns, anomalies, and trends
- Generates textual summaries of findings

#### 5. Visualization (Enhanced)
- Extends existing visualization in `gen_graph.py`
- Adds new visualization types while maintaining current functionality
- Ensures visual consistency with existing graphs

## Implementation Details

### File Structure
```
trust-pilot-parser/
├── trustpilot_scraper.py (existing)
├── gen_graph.py (existing)
├── analysis/
│   ├── __init__.py
│   ├── processor.py (data preprocessing)
│   ├── temporal.py (time analysis)
│   ├── content.py (text analysis)
│   ├── ratings.py (rating analysis)
│   └── behavior.py (customer behavior)
├── insights/
│   ├── __init__.py
│   └── generator.py
└── visualization/
    ├── __init__.py
    └── extended_graphs.py
```

### Key Interfaces

#### Analysis Module Interface
```python
class AnalysisModule:
    """Base class for all analysis modules"""
    
    def __init__(self, config=None):
        self.config = config or {}
        
    def analyze(self, data):
        """Analyze the data and return results
        
        Args:
            data: JSON review data loaded from file
            
        Returns:
            dict: Analysis results
        """
        raise NotImplementedError
        
    def get_metadata(self):
        """Return metadata about this analysis module
        
        Returns:
            dict: Module metadata
        """
        return {
            "name": self.__class__.__name__,
            "description": self.__doc__
        }
```

#### Insight Generator Interface
```python
class InsightGenerator:
    """Generates insights from analysis results"""
    
    def __init__(self, config=None):
        self.config = config or {}
        
    def generate_insights(self, analysis_results):
        """Generate insights from analysis results
        
        Args:
            analysis_results: Dict of results from analysis modules
            
        Returns:
            dict: Generated insights
        """
        raise NotImplementedError
```

### Integration with Existing Code

#### Integration with gen_graph.py
The existing graph generation code will remain unchanged, but will be extended through a new module that inherits or imports functionality from the original.

```python
from gen_graph import generate_graph

def enhanced_generate_graph(input_file=None, output_file=None, analysis_results=None):
    """Enhanced version of generate_graph with additional visualizations"""
    # First generate the original graphs
    generate_graph(input_file, output_file)
    
    # Then add additional visualizations based on analysis_results
    if analysis_results:
        # Add new visualizations here
        pass
```

#### Command-Line Interface Extension
The system will extend the existing CLI interface with new options for analysis:

```
python analysis_runner.py --input tp_bhg_reviews.json --modules temporal,content,ratings --output analysis_results.json
```

## Data Flow

1. Reviews are extracted using the existing `trustpilot_scraper.py` (no changes)
2. JSON data is loaded through an extended version of the current loading mechanism
3. Analysis modules process the data to extract patterns and insights
4. The Insight Generator compiles results into actionable recommendations
5. Enhanced visualization extends the existing graphs with new insights

## Performance Considerations

### Large Dataset Handling
- Implement streaming processing for large JSON files
- Process reviews in batches to minimize memory usage
- Cache intermediate results for expensive operations

### Text Analysis Optimization
- Implement efficient text preprocessing pipeline
- Use sampling techniques for topic modeling with large datasets
- Apply optimized tokenization and natural language processing

## Testing Strategy

### Unit Testing
- Test each analysis module independently
- Verify correct preprocessing of review data
- Validate statistical calculations

### Integration Testing
- Test integration with existing code
- Verify end-to-end workflow

### Performance Testing
- Test with the largest available review datasets
- Benchmark memory usage and processing time

## Deployment Considerations

### Installation
- Provide clear documentation for installing new dependencies
- Update the project's Python requirements

### Usage Documentation
- Create documentation for new analysis capabilities
- Provide examples of how to interpret results

### Error Handling
- Implement robust error handling for all analysis components
- Log errors to the existing logging mechanism
- Provide graceful degradation when errors occur 