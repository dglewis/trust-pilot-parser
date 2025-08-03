# Trustpilot External Data Access Policy Analysis

## Executive Summary

This document analyzes Trustpilot's official policies regarding automated data access and web scraping. The investigation reveals that Trustpilot explicitly prohibits automated data collection and web scraping through multiple policy mechanisms, while providing official APIs as the sanctioned method for accessing their data.

## 1. Robots.txt Analysis

### Overview
Trustpilot maintains a comprehensive robots.txt file at `https://www.trustpilot.com/robots.txt` that provides detailed instructions for automated crawlers and bots.

### Key Findings

#### 1.1 Search Engine Bot Permissions
The robots.txt file allows major search engines and social media platforms to access specific content:
- **Allowed Bots**: Googlebot, Mediapartners-Google, Googlebot-Mobile, AdsBot-Google, bingbot, msnbot, ia_archiver, Alexabot, ScoutJet, Slurp, Twitterbot, Baiduspider, DuckDuckBot
- **Limited Access**: Most bots are restricted from accessing `/reviews/` and `/api/*` endpoints
- **Special Permission**: FacebookBot and facebookexternalhit are explicitly allowed to access `/reviews/` content

#### 1.2 AI and ML Bot Restrictions
Trustpilot explicitly blocks all major AI and machine learning bots:
- ChatGPT-User, OAI-SearchBot, PerplexityBot
- Claude-User, Claude-SearchBot, ClaudeBot
- GPTBot, Google-Extended, Applebot-Extended
- anthropic-ai, cohere-ai, CCBot, Bytespider
- Meta-ExternalAgent, Meta-ExternalFetcher

#### 1.3 Comprehensive Restrictions
The robots.txt file contains extensive restrictions including:
- **Disallowed Paths**: `/error`, `/evaluate/`, `/api/*`, `/search`, `/users/`
- **Query Parameter Restrictions**: `/*?*stars=`, `/*?*sort=`, `/*?*verified=`, etc.
- **Universal Block**: `User-agent: *` followed by `Disallow: /` blocks all unspecified bots

#### 1.4 Notable Exclusions
Several categories of bots are completely blocked:
- Scraping bots (sentibot, Diffbot, ImagesiftBot)
- Data collection services (AwarioRssBot, AwarioSmartBot, Webzio-Extended)
- General crawlers (Yandex, Omgilibot, Kangaroo Bot, YouBot, Timpibot)

### 1.5 Sitemap References
The robots.txt file includes sitemap references for legitimate indexing:
- `https://sitemaps.trustpilot.com/index_en-us.xml`
- `https://trustpilot.com/trust/sitemaps/domain_en-us.xml`
- `https://trustpilot.com/blog/sitemaps/domain_en-us.xml`

## 2. Official API Investigation

### 2.1 Trustpilot Developer Platform
Trustpilot operates an official developer platform at `https://developers.trustpilot.com/` with comprehensive API documentation.

#### Available APIs:
1. **Trustpilot for Business API**
   - Business Units API (public and private endpoints)
   - Service Reviews API
   - Product Reviews API
   - Invitations API
   - Consumer API

2. **Integration Partners Program**
   - Partner integration support
   - Authorized reseller programs
   - Third-party integrations

3. **Data Solutions API (New)**
   - Access to Trustpilot's global database
   - Business profiles and consumer reviews
   - Structured data access

### 2.2 Authentication Requirements
All official APIs require:
- API key authentication
- OAuth tokens for business user functions
- Rate limiting compliance
- Adherence to usage guidelines

### 2.3 Legitimate Data Access Methods
Trustpilot provides several sanctioned access methods:
- **Public APIs**: For accessing publicly available review data
- **Business APIs**: For businesses to manage their profiles and reviews
- **Partner APIs**: For authorized integration partners
- **Data Licensing**: For large-scale data access needs

## 3. Terms of Service Analysis

### 3.1 Explicit Scraping Prohibitions
Trustpilot's Terms of Use contain explicit prohibitions against automated data collection:

#### For Businesses (Section 21):
> "Access, search, or collect content from our platform or services by any means (automated or otherwise) except as permitted in these terms or otherwise authorised by us. Without limiting the previous statement, you must not carry out, facilitate, authorise or permit any text or data mining or web scraping in relation to our platform or services for any purpose, including the development, training, fine-tuning or validation of artificial intelligence systems or models, and we do not consent to the use of our platform or services for these purposes."

#### For Consumers (Section 4):
> "You must not access, search or collect content from our platform by any means (automated or otherwise) except as provided on our platform or specifically approved by us. You must not carry out in any way (including facilitating, permitting or authorising) any text mining, data mining or web scraping of our platform for any purpose without our express permission. This includes the training and development of artificial intelligence systems or models."

### 3.2 Additional Restrictions
- Prohibition of reverse engineering platform components
- Restrictions on copying, distributing, or modifying content
- Explicit consent required for automated data collection
- Special restrictions on AI/ML training data collection

### 3.3 Intellectual Property Protection
Trustpilot claims ownership of:
- Platform design and compilation
- TrustScores and review aggregations
- Proprietary algorithms and methodologies
- Brand marks and trademarks

## 4. Content Refresh Guidelines

### 4.1 Authorized Data Usage
For authorized partners and customers, Trustpilot maintains strict guidelines:
- Content must be refreshed within 24 hours of changes
- Real-time API access preferred over cached content
- Specific licensing agreements required
- Compliance monitoring and auditing

### 4.2 Partner Requirements
- Valid partner agreements mandatory
- Limited non-exclusive licenses only
- Subscription to paid services required for content usage
- Adherence to refresh and accuracy requirements

## 5. Summary and Recommendations

### 5.1 Policy Compliance Assessment
Based on this investigation, the current scraping approach appears to **violate multiple explicit policies**:

1. **Robots.txt Violations**: The universal `Disallow: /` directive prohibits all unauthorized automated access
2. **Terms of Service Violations**: Explicit prohibitions against web scraping and automated data collection
3. **AI/ML Restrictions**: Specific blocks against AI training data collection
4. **Intellectual Property Concerns**: Unauthorized use of proprietary content and algorithms

### 5.2 Recommended Alternatives

#### Immediate Actions:
1. **Discontinue Scraping**: Cease all automated data collection activities
2. **Evaluate API Options**: Investigate official API access for legitimate use cases
3. **Consider Data Licensing**: For research purposes, explore academic licensing options

#### Long-term Solutions:
1. **Partner Program**: Apply for Trustpilot's integration partner program if applicable
2. **Business Account**: Establish a business relationship for authorized data access
3. **Academic Collaboration**: Reach out to Trustpilot for research partnership opportunities

### 5.3 Risk Assessment
Continuing current scraping activities presents several risks:
- **Legal Action**: Potential cease-and-desist orders or legal proceedings
- **Technical Countermeasures**: IP blocking, CAPTCHAs, or other anti-scraping measures
- **Ethical Concerns**: Violation of clearly stated website policies
- **Data Quality Issues**: Unofficial data may be incomplete or unreliable

### 5.4 Ethical Considerations
Trustpilot's policies reflect legitimate concerns about:
- Platform integrity and performance
- User privacy and data protection
- Intellectual property rights
- Business model sustainability

## Conclusion

Trustpilot has established comprehensive policies that explicitly prohibit unauthorized automated data access and web scraping. These policies are enforced through technical measures (robots.txt), legal frameworks (Terms of Service), and business practices (API requirements). 

The company provides legitimate alternatives through official APIs and partnership programs, indicating their willingness to provide data access through proper channels. Any continued scraping activities would clearly violate their stated policies and could result in legal or technical consequences.

**Recommendation**: Immediately transition to official API access methods or discontinue data collection activities to ensure compliance with Trustpilot's policies.

---

*Document compiled from official Trustpilot sources as of January 2025*