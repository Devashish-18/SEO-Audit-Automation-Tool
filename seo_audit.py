import json
import re
from collections import Counter
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup


def crawl_page(url):
    """
    Crawls the given URL and returns the HTML content.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return f"Error crawling {url}: {str(e)}"


def parse_schema_blocks(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    schema_blocks = []
    scripts = soup.find_all('script', type=lambda value: value and 'ld+json' in value.lower())

    for script in scripts:
        raw_text = script.string or script.get_text() or ''
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            continue

        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if not isinstance(item, dict):
                continue
            schema_blocks.append({
                'type': item.get('@type') or item.get('type') or 'Unknown',
                'raw': item,
            })

    return schema_blocks


def analyze_header_hierarchy(soup: BeautifulSoup) -> Dict[str, Any]:
    headings = []
    issues = []

    for tag in soup.find_all(re.compile('^h[1-6]$', re.IGNORECASE)):
        level = int(tag.name[1])
        headings.append({
            'tag': tag.name.lower(),
            'level': level,
            'text': tag.get_text(' ', strip=True),
        })

    h1_count = sum(1 for heading in headings if heading['tag'] == 'h1')
    if h1_count == 0:
        issues.append('Missing H1 tag.')
    elif h1_count > 1:
        issues.append('Multiple H1 tags found.')

    if headings and headings[0]['level'] != 1:
        issues.append(f"First heading is {headings[0]['tag'].upper()} rather than H1.")

    previous_level = None
    for heading in headings:
        if previous_level is not None and heading['level'] > previous_level + 1:
            issues.append(f"Header hierarchy jump from H{previous_level} to H{heading['level']}.")
        previous_level = heading['level']

    return {
        'headings': headings,
        'issues': issues,
    }


def analyze_image_attributes(soup: BeautifulSoup) -> Dict[str, Any]:
    images = soup.find_all('img')
    details = []
    missing_alt = 0
    missing_title = 0

    for img in images:
        src = img.get('src', '').strip()
        alt = (img.get('alt') or '').strip()
        title = (img.get('title') or '').strip()

        if not alt:
            missing_alt += 1
            details.append({'src': src, 'issue': 'Missing alt text'})
        if not title:
            missing_title += 1
            details.append({'src': src, 'issue': 'Missing title attribute'})

    return {
        'total_images': len(images),
        'missing_alt': missing_alt,
        'missing_title': missing_title,
        'details': details,
    }


def analyze_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
    title_tag = soup.find('title')
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})

    title = title_tag.text.strip() if title_tag else None
    description = meta_desc['content'].strip() if meta_desc and meta_desc.get('content') else None
    keywords = [keyword.strip() for keyword in meta_keywords['content'].split(',')] if meta_keywords and meta_keywords.get('content') else []

    issues = []
    if not title:
        issues.append('Missing title tag.')
    if not description:
        issues.append('Missing meta description.')
    if not keywords:
        issues.append('Missing meta keywords tag.')

    return {
        'title': title,
        'description': description,
        'keywords': keywords,
        'issues': issues,
    }


def analyze_keyword_usage(soup: BeautifulSoup, keywords: List[str]) -> Dict[str, Any]:
    text = soup.get_text(' ', strip=True).lower()
    keyword_counts = {}
    issues = []

    for keyword in keywords:
        normalized = keyword.lower()
        keyword_counts[keyword] = text.count(normalized)

    if not keywords:
        issues.append('No meta keywords provided for keyword usage analysis.')
    else:
        missing_in_body = [kw for kw, count in keyword_counts.items() if count == 0]
        if missing_in_body:
            issues.append(f"The following keywords are not present in the page text: {', '.join(missing_in_body)}.")

    return {
        'meta_keywords': keywords,
        'keyword_counts': keyword_counts,
        'issues': issues,
    }


def extract_metrics(html_content: str, url: str) -> Dict[str, Any]:
    """
    Extracts key SEO metrics from the HTML content.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    metrics: Dict[str, Any] = {}

    title_tag = soup.find('title')
    metrics['title'] = title_tag.text.strip() if title_tag else None

    meta_desc = soup.find('meta', attrs={'name': 'description'})
    metrics['meta_description'] = meta_desc['content'].strip() if meta_desc and meta_desc.get('content') else None

    h1_tags = soup.find_all('h1')
    metrics['h1_count'] = len(h1_tags)
    metrics['h1_texts'] = [tag.get_text(' ', strip=True) for tag in h1_tags]

    image_analysis = analyze_image_attributes(soup)
    metrics.update(image_analysis)

    links = soup.find_all('a', href=True)
    internal_links = [link for link in links if link['href'].startswith('/') or (url and link['href'].startswith(url))]
    external_links = [link for link in links if link['href'].startswith('http') and not (url and link['href'].startswith(url))]
    metrics['internal_links'] = len(internal_links)
    metrics['external_links'] = len(external_links)

    viewport = soup.find('meta', attrs={'name': 'viewport'})
    metrics['has_viewport'] = viewport is not None

    metrics['header_hierarchy'] = analyze_header_hierarchy(soup)
    metrics['metadata_analysis'] = analyze_metadata(soup)
    metrics['keyword_analysis'] = analyze_keyword_usage(soup, metrics['metadata_analysis']['keywords'])
    metrics['schema_blocks'] = parse_schema_blocks(soup)

    return metrics


def calculate_score(metrics: Dict[str, Any]) -> int:
    """
    Calculates a simple SEO score based on the extracted metrics.
    Returns a score out of 100.
    """
    score = 0

    if metrics.get('title'):
        score += 20
    if metrics.get('meta_description'):
        score += 15

    header_issues = metrics.get('header_hierarchy', {}).get('issues', [])
    if not header_issues:
        score += 15
    elif any('Missing H1' in issue or 'Multiple H1' in issue for issue in header_issues):
        score += 5

    if metrics.get('missing_alt') == 0:
        score += 10
    else:
        score += max(0, 10 - min(metrics.get('missing_alt', 0) * 3, 10))

    if metrics.get('missing_title') == 0:
        score += 5

    if metrics['internal_links'] > metrics['external_links']:
        score += 10
    elif metrics['internal_links'] == metrics['external_links']:
        score += 5

    if metrics.get('has_viewport'):
        score += 10

    if metrics.get('schema_blocks'):
        score += 10

    score = max(0, min(100, score))
    return score


def generate_suggestions(metrics: Dict[str, Any]) -> List[str]:
    """
    Generates SEO improvement suggestions based on the metrics.
    """
    suggestions: List[str] = []

    if not metrics.get('title'):
        suggestions.append('Add a descriptive title tag to improve search engine visibility.')
    if not metrics.get('meta_description'):
        suggestions.append('Include a meta description tag to provide a summary for search results.')

    header_issues = metrics.get('header_hierarchy', {}).get('issues', [])
    for issue in header_issues:
        if 'Missing H1' in issue:
            suggestions.append('Add exactly one H1 tag at the top of the page.')
        elif 'Multiple H1' in issue:
            suggestions.append('Limit to a single H1 tag and use H2/H3 for subheads.')
        elif 'jump from' in issue.lower():
            suggestions.append('Keep header levels sequential to preserve semantic hierarchy (H2 after H1, H3 after H2).')

    if metrics.get('missing_alt', 0) > 0:
        suggestions.append(f'Add alt text to {metrics.get("missing_alt", 0)} image(s) for accessibility and SEO.')
    if metrics.get('missing_title', 0) > 0:
        suggestions.append(f'Add title attributes to {metrics.get("missing_title", 0)} image(s) if descriptions help clarify image purpose.')

    metadata_issues = metrics.get('metadata_analysis', {}).get('issues', [])
    for issue in metadata_issues:
        if 'Missing title' in issue:
            suggestions.append('Ensure the page includes a unique <title> tag.')
        if 'Missing meta description' in issue:
            suggestions.append('Add a meta description tag to summarize the page for search results.')
        if 'Missing meta keywords' in issue:
            suggestions.append('If you use meta keywords, add them in a comma-separated keywords meta tag.')

    keyword_issues = metrics.get('keyword_analysis', {}).get('issues', [])
    for issue in keyword_issues:
        suggestions.append(issue)

    if not metrics.get('schema_blocks'):
        suggestions.append('Add JSON-LD schema markup for key entities like Organization, Website, or Article.')
    else:
        schema_types = [block.get('type', 'Unknown') for block in metrics.get('schema_blocks', [])]
        suggestions.append(f'Detected schema types: {", ".join(schema_types)}. Verify they match the page intent.')

    return suggestions
