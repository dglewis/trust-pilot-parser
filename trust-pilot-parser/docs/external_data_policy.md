# External Data Policy and Compliance Guidelines

## Overview

This document outlines the policy and legal considerations for extracting data from external websites, with specific focus on Trustpilot compliance. It is essential to understand and follow these guidelines to ensure legal and ethical data collection practices.

## Legal Framework

### 1. Robots.txt Compliance

#### What is robots.txt?
The robots.txt file is a web standard that instructs web crawlers and bots on which parts of a website they are allowed to access. While not legally binding, respecting robots.txt demonstrates good faith compliance with website owners' wishes.

#### Trustpilot's robots.txt Analysis
As of our last review, Trustpilot's robots.txt contains:
- `User-agent: * Disallow: /` - This prohibits ALL general automated access
- Specific allowances only for major search engines (Google, Bing, etc.)
- Explicit blocking of AI/ML bots (GPTBot, ClaudeBot, etc.)
- Disallowance of review pages (`/reviews/`) for most bots

**Compliance Status**: ❌ **NON-COMPLIANT** - Current scraper violates robots.txt

### 2. Terms of Service Analysis

#### Trustpilot's Terms Prohibit:
1. **Automated data collection** without explicit permission
2. **Text or data mining** for any purpose
3. **Web scraping** activities
4. **AI/ML training data collection**
5. **Commercial exploitation** of scraped data

#### Key Violations:
- Section 4 (Consumer Terms): Prohibits automated access
- Section 21 (Business Terms): Explicitly bans scraping and data mining

**Compliance Status**: ❌ **NON-COMPLIANT** - Violates multiple ToS sections

## Recommendations

### Option 1: Use Official API (RECOMMENDED)
- **Trustpilot Business API**: Available for legitimate business purposes
- **Proper Authentication**: Requires API keys and business account
- **Rate Limits**: Built-in compliance with acceptable usage
- **Legal Coverage**: Covered under business terms of service

### Option 2: Cease Trustpilot Scraping
- **Risk Mitigation**: Eliminates legal exposure
- **Alternative Sources**: Consider other review platforms with permissive policies
- **Public Data**: Focus on truly public, unrestricted data sources

### Option 3: Seek Explicit Permission (COMPLEX)
- **Written Agreement**: Formal data access agreement with Trustpilot
- **Limited Scope**: Likely restricted use cases
- **Commercial Terms**: Potential licensing fees

## Implementation Guidelines

### If Continuing with Scraping (NOT RECOMMENDED)

⚠️ **WARNING**: The following guidelines do NOT make scraping Trustpilot legal or compliant, but represent harm reduction principles if scraping continues despite recommendations.

#### Rate Limiting
- **Minimum Delays**: 30+ seconds between requests
- **Respectful Timing**: Avoid peak business hours
- **Circuit Breakers**: Stop if rate limited or blocked

#### Technical Requirements
- **Proper User Agent**: Identify your bot clearly
- **Respect Headers**: Honor rate limit and cache headers
- **Error Handling**: Graceful failure and retry logic

#### Legal Protections
- **Research Purpose**: Limit to academic/research use only
- **No Commercial Use**: Avoid any commercial exploitation
- **Data Minimization**: Collect only necessary data
- **Secure Storage**: Implement data protection measures

## Risk Assessment

### Legal Risks
1. **Cease and Desist**: Trustpilot may demand cessation of activities
2. **Account Termination**: Business accounts may be suspended
3. **Legal Action**: Potential for breach of contract claims
4. **Technical Blocking**: IP-based blocking and countermeasures

### Technical Risks
1. **Detection Systems**: Advanced bot detection may identify scrapers
2. **Rate Limiting**: Aggressive limiting may make scraping ineffective
3. **Structure Changes**: Website changes can break scrapers
4. **Resource Costs**: Increased infrastructure costs for compliance

### Reputational Risks
1. **Industry Relations**: Potential impact on business relationships
2. **Trustpilot Relationship**: Damage to potential partnership opportunities
3. **Legal Precedent**: Setting precedent for non-compliance

## Compliance Checklist

### Before Any Data Collection:
- [ ] Review target website's robots.txt
- [ ] Read and analyze terms of service
- [ ] Check for available APIs or official data access
- [ ] Assess legal risks and business justification
- [ ] Document compliance reasoning and limitations

### Technical Implementation:
- [ ] Implement robots.txt checker
- [ ] Configure appropriate user agent
- [ ] Set respectful crawl delays (minimum 30 seconds)
- [ ] Implement rate limiting and circuit breakers
- [ ] Add error handling and graceful degradation
- [ ] Log all activities for audit purposes

### Ongoing Monitoring:
- [ ] Regular review of robots.txt changes
- [ ] Monitor for terms of service updates
- [ ] Track for cease and desist communications
- [ ] Review data collection practices quarterly
- [ ] Maintain legal compliance documentation

## Data Handling Principles

### Collection
- **Minimal Scope**: Collect only publicly available data
- **Purpose Limitation**: Clearly defined use cases
- **Time Limitation**: Regular data purging schedules

### Storage
- **Security**: Encrypted storage and transmission
- **Access Control**: Limited access on need-to-know basis
- **Retention**: Clear data retention policies
- **Backup**: Secure backup procedures

### Usage
- **Attribution**: Proper source attribution
- **Anonymization**: Remove or anonymize personal data
- **Aggregation**: Use aggregated data where possible
- **No Re-identification**: Avoid attempts to identify individuals

## Alternative Data Sources

### Review Platform APIs
- **Google My Business API**: Legitimate access to Google reviews
- **Yelp Fusion API**: Official Yelp review data
- **Facebook Graph API**: Facebook review data
- **Amazon Product Advertising API**: Amazon review data

### Public Data Sources
- **Government Databases**: Regulatory complaints and filings
- **Academic Datasets**: Research-grade review datasets
- **Open Source Projects**: Community-maintained review collections

### Commercial Data Providers
- **Review Aggregators**: Licensed review data providers
- **Market Research**: Professional market research services
- **Data Brokers**: Licensed commercial data sources

## Contact Information

For questions about this policy or compliance concerns:
- Technical Lead: [Your contact information]
- Legal Counsel: [Legal contact information]
- Compliance Officer: [Compliance contact information]

## Document History

- **Version 1.0**: Initial policy creation
- **Last Updated**: [Current date]
- **Next Review**: [Schedule quarterly reviews]

---

**DISCLAIMER**: This document provides guidance but does not constitute legal advice. Consult with qualified legal counsel before implementing any web scraping activities. The legal landscape around web scraping is complex and evolving.