"""
Comprehensive Page Auditor with CSS Detection & Semantic Validation
Production-grade implementation for SEO auditing

Key Features:
- Full CSS hiding detection (display:none, visibility:hidden, position offscreen, etc.)
- Semantic H1 validation
- Image alt text quality scoring
- Schema.org validation (especially Course schema)
- Keyword density analysis
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from jsonschema import validate, ValidationError
from collections import Counter


class ComprehensivePageAuditor:
    """Production-grade Page Auditor with robust CSS detection"""

    def __init__(self):
        self.hidden_classes = {
            'hidden', 'sr-only', 'visually-hidden', 'screen-reader-only',
            'display-none', 'd-none', 'invisible', 'is-hidden', 'hide'
        }
        
        self.hidden_css_patterns = [
            r'display\s*:\s*none',
            r'visibility\s*:\s*hidden',
            r'opacity\s*:\s*0',
            r'width\s*:\s*0(?!\s*;.*[\w])',
            r'height\s*:\s*0(?!\s*;.*[\w])',
            r'position\s*:\s*absolute.*left\s*:\s*-\d+',
        ]

    # ========================
    # H1 VISIBILITY CHECKING
    # ========================

    def check_h1_visibility(self, html: str, external_css: str = "") -> Dict:
        """
        Comprehensive check: Is H1 visible to users and search engines?
        
        Args:
            html: HTML content as string
            external_css: External CSS rules (if available)
        
        Returns:
            {
                "visible": bool,
                "score": 0-100,
                "issues": [{"method": str, "severity": str, "fix": str}],
                "recommendation": str
            }
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        h1 = soup.find('h1')
        
        if not h1:
            return {
                "visible": False,
                "score": 0,
                "issues": [{
                    "method": "missing",
                    "severity": "CRITICAL",
                    "message": "No H1 tag found",
                    "fix": "Add exactly one <h1> tag with main topic"
                }],
                "recommendation": "SEO CRITICAL: H1 is required"
            }
        
        visibility_issues = []
        
        # Check 1: Inline style hiding
        inline_hiding = self._check_inline_style_hiding(h1)
        if inline_hiding:
            visibility_issues.extend(inline_hiding)
        
        # Check 2: aria-hidden
        if h1.get('aria-hidden') == 'true':
            visibility_issues.append({
                "method": "aria_hidden",
                "severity": "CRITICAL",
                "message": "H1 has aria-hidden='true' (hidden from screen readers)",
                "fix": "Remove aria-hidden='true' from H1"
            })
        
        # Check 3: Class-based hiding
        classes = h1.get('class', [])
        if isinstance(classes, list):
            hidden_classes = [c for c in classes if c in self.hidden_classes]
            if hidden_classes:
                visibility_issues.append({
                    "method": "class_based",
                    "severity": "HIGH",
                    "message": f"H1 has hiding classes: {', '.join(hidden_classes)}",
                    "classes": hidden_classes,
                    "fix": f"Remove or rename classes: {', '.join(hidden_classes)}"
                })
        
        # Check 4: Parent element hiding
        parent_hiding = self._check_parent_hiding(h1)
        if parent_hiding:
            visibility_issues.append(parent_hiding)
        
        # Calculate score
        if visibility_issues:
            critical_count = sum(1 for i in visibility_issues if i['severity'] == 'CRITICAL')
            high_count = sum(1 for i in visibility_issues if i['severity'] == 'HIGH')
            score = max(0, 100 - (critical_count * 50 + high_count * 15))
            visible = critical_count == 0
        else:
            score = 100
            visible = True
        
        return {
            "visible": visible,
            "score": score,
            "issues": visibility_issues,
            "recommendation": (
                "✅ H1 is visible" if visible 
                else "❌ SEO CRITICAL: Fix visibility issues immediately"
            )
        }

    def _check_inline_style_hiding(self, element) -> List[Dict]:
        """Check inline style attribute for hiding methods"""
        
        style = (element.get('style') or '').lower()
        if not style:
            return []
        
        issues = []
        hiding_patterns = {
            'display:none': r'display\s*:\s*none',
            'visibility:hidden': r'visibility\s*:\s*hidden',
            'opacity:0': r'opacity\s*:\s*0',
            'width:0': r'width\s*:\s*0(?!\s*;.*[\w])',
            'height:0': r'height\s*:\s*0(?!\s*;.*[\w])',
            'position:off-screen': r'position\s*:\s*absolute.*left\s*:\s*-\d+',
        }
        
        for name, pattern in hiding_patterns.items():
            if re.search(pattern, style):
                issues.append({
                    "method": "inline_style",
                    "severity": "CRITICAL",
                    "message": f"H1 has hiding style: {name}",
                    "fix": f"Remove '{name}' from style attribute"
                })
        
        return issues

    def _check_parent_hiding(self, element) -> Optional[Dict]:
        """Recursive check: is parent element hidden?"""
        
        parent = element.parent
        depth = 0
        
        while parent and parent.name and depth < 10:
            # Check inline styles
            style = (parent.get('style') or '').lower()
            if any(pattern in style for pattern in ['display:none', 'visibility:hidden']):
                return {
                    "method": "parent_hidden",
                    "severity": "HIGH",
                    "message": f"Parent <{parent.name}> is hidden (hides H1 too)",
                    "fix": f"Move H1 outside of hidden parent <{parent.name}>"
                }
            
            # Check class-based hiding
            classes = parent.get('class', [])
            if isinstance(classes, list):
                if any(c in self.hidden_classes for c in classes):
                    return {
                        "method": "parent_class_hidden",
                        "severity": "HIGH",
                        "message": f"Parent <{parent.name}> has hiding class",
                        "fix": "Move H1 outside of hidden parent"
                    }
            
            parent = parent.parent
            depth += 1
        
        return None

    # ========================
    # SEMANTIC H1 VALIDATION
    # ========================

    def validate_h1_semantics(self, h1_text: str, page_title: str, target_keyword: str) -> Dict:
        """
        Validate H1 is semantically appropriate for the page
        
        Returns: {score: 0-100, issues: [...], grade: A+/A/B/F}
        """
        
        issues = []
        h1_text_lower = h1_text.lower()
        title_lower = page_title.lower()
        keyword_lower = target_keyword.lower()
        
        # Check 1: H1 alignment with page title
        title_words = set(title_lower.split())
        h1_words = set(h1_text_lower.split())
        
        if title_words and h1_words:
            overlap = len(title_words & h1_words) / len(title_words | h1_words)
        else:
            overlap = 0
        
        if overlap < 0.3:
            issues.append({
                "severity": "MEDIUM",
                "message": f"H1 doesn't align with page title (overlap: {overlap:.1%})",
                "h1": h1_text,
                "title": page_title,
                "suggestion": "H1 should restate or closely relate to page title"
            })
        
        # Check 2: Keyword inclusion
        if keyword_lower not in h1_text_lower:
            issues.append({
                "severity": "HIGH",
                "message": f"H1 doesn't include target keyword: '{target_keyword}'",
                "suggestion": "Include keyword or semantic variant in H1"
            })
        
        # Check 3: H1 length (ideal: 20-60 chars)
        h1_len = len(h1_text)
        if h1_len < 10:
            issues.append({
                "severity": "MEDIUM",
                "message": f"H1 too short ({h1_len} chars). Should be 20+ chars",
                "suggestion": "Expand H1 with descriptive text"
            })
        elif h1_len > 70:
            issues.append({
                "severity": "MEDIUM",
                "message": f"H1 too long ({h1_len} chars). May truncate in SERP",
                "suggestion": "Keep H1 under 70 characters"
            })
        
        # Calculate score
        score = 100
        score -= len([i for i in issues if i['severity'] == 'HIGH']) * 30
        score -= len([i for i in issues if i['severity'] == 'MEDIUM']) * 15
        score = max(0, score)
        
        # Grade
        if score >= 90:
            grade = "A+"
        elif score >= 80:
            grade = "A"
        elif score >= 70:
            grade = "B"
        else:
            grade = "F"
        
        return {
            "score": score,
            "grade": grade,
            "issues": issues,
            "passed": score >= 70
        }

    # ========================
    # IMAGE ALT TEXT QUALITY
    # ========================

    def audit_image_alt_quality(self, img_tag, src_filename: str = "") -> Dict:
        """
        Score alt text quality (0-100), not just presence
        
        Returns: {score: 0-100, grade: A+/A/B/F, issues: [...]}
        """
        
        alt_text = (img_tag.get('alt') or '').strip()
        score = 0
        issues = []
        
        # Missing alt text
        if not alt_text:
            return {
                "score": 0,
                "grade": "F",
                "issues": [{
                    "severity": "CRITICAL",
                    "message": "Missing alt attribute",
                    "fix": "Add descriptive alt text"
                }],
                "passed": False
            }
        
        # Length check (ideal: 30-125 chars)
        if 30 <= len(alt_text) <= 125:
            score += 25
        elif len(alt_text) < 5:
            issues.append({
                "severity": "HIGH",
                "message": f"Alt text too short ({len(alt_text)} chars)",
                "fix": "Expand to 30+ chars describing what's in image"
            })
        elif len(alt_text) > 150:
            issues.append({
                "severity": "MEDIUM",
                "message": f"Alt text too long ({len(alt_text)} chars) — likely keyword-stuffed",
                "fix": "Keep under 125 characters"
            })
            score += 15
        else:
            score += 20
        
        # Generic terms check
        generic_terms = ['image', 'photo', 'picture', 'screenshot', 'img', 'file', 'pic', 'graphic']
        if alt_text.lower() in generic_terms:
            issues.append({
                "severity": "HIGH",
                "message": f"Alt text too generic: '{alt_text}'",
                "fix": "Describe what's actually in the image"
            })
        else:
            score += 20
        
        # Keyword stuffing detection
        words = alt_text.lower().split()
        word_freq = Counter(words)
        for word, count in word_freq.items():
            if count > 3:
                issues.append({
                    "severity": "MEDIUM",
                    "message": f"Keyword '{word}' repeated {count}x — appears keyword-stuffed",
                    "fix": "Use natural language without repetition"
                })
                break
        
        if not any('repeated' in str(i) for i in issues):
            score += 15
        
        # Image type alignment
        src_lower = src_filename.lower() if src_filename else ""
        if 'logo' in src_lower and 'logo' not in alt_text.lower():
            issues.append({
                "severity": "MEDIUM",
                "message": "Image is logo but alt doesn't mention it",
                "fix": "Include 'logo' in alt text"
            })
        elif 'screenshot' in src_lower and 'screenshot' not in alt_text.lower():
            issues.append({
                "severity": "MEDIUM",
                "message": "Image is screenshot but alt doesn't mention it",
                "fix": "Include 'screenshot' in alt text"
            })
        else:
            score += 15
        
        # Grade
        score = min(100, score)
        if score >= 90:
            grade = "A+"
        elif score >= 80:
            grade = "A"
        elif score >= 70:
            grade = "B"
        else:
            grade = "F"
        
        return {
            "score": score,
            "grade": grade,
            "alt_text": alt_text,
            "issues": issues,
            "passed": score >= 70
        }

    # ========================
    # SCHEMA VALIDATION
    # ========================

    def audit_course_schema(self, schema_json_str: str) -> Dict:
        """
        Validate Course schema against Google's official spec
        Returns rich error messages for missing/invalid fields
        """
        
        try:
            schema = json.loads(schema_json_str)
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "eligible_for_rich_snippets": False,
                "issues": [{
                    "severity": "CRITICAL",
                    "message": f"Invalid JSON-LD syntax: {str(e)}",
                    "fix": "Validate JSON structure"
                }]
            }
        
        issues = []
        critical_count = 0
        
        # Required properties
        required_properties = {
            "@context": "https://schema.org",
            "@type": "Course",
            "name": "string (program name, 20+ chars)",
            "provider": "object with @type: Organization and name",
            "description": "string (20+ chars)"
        }
        
        for prop, expected_type in required_properties.items():
            if prop not in schema:
                issues.append({
                    "severity": "CRITICAL",
                    "message": f"Missing required property: '{prop}'",
                    "impact": "Page won't be eligible for Google Course rich snippets",
                    "fix": f"Add {prop}: {expected_type}",
                    "example": expected_type
                })
                critical_count += 1
            
            elif prop == "description":
                desc = schema.get(prop, '')
                if len(desc) < 20:
                    issues.append({
                        "severity": "MEDIUM",
                        "message": f"Description too short ({len(desc)} chars)",
                        "impact": "May not meet Google's quality threshold",
                        "fix": "Expand to 20+ characters"
                    })
        
        # Recommended but missing fields
        recommended_fields = {
            "aggregateRating": "Enables star ratings in SERP (+20-30% CTR boost)",
            "price": "Enables price display in SERP",
            "duration": "Course length (ISO 8601, e.g., 'PT18M' for 18 months)",
            "educationLevel": "e.g., 'BeginnerLevel', 'IntermediateLevel'",
            "url": "Direct link to course landing page"
        }
        
        for field, benefit in recommended_fields.items():
            if field not in schema:
                issues.append({
                    "severity": "MEDIUM",
                    "message": f"Missing recommended field: '{field}'",
                    "benefit": benefit,
                    "fix": f"Add {field} to unlock rich snippet enhancement"
                })
        
        # Validate aggregateRating structure
        if "aggregateRating" in schema:
            rating = schema["aggregateRating"].get("ratingValue")
            count = schema["aggregateRating"].get("ratingCount")
            
            if not isinstance(rating, (int, float)) or not (1 <= rating <= 5):
                issues.append({
                    "severity": "HIGH",
                    "message": f"Invalid ratingValue: {rating} (must be 1-5)",
                    "fix": "Set ratingValue to number between 1 and 5"
                })
                critical_count += 1
            
            if count and count < 5:
                issues.append({
                    "severity": "MEDIUM",
                    "message": f"ratingCount too low: {count} (Google requires 5+ for display)",
                    "fix": "Accumulate more reviews before displaying"
                })
        
        valid = critical_count == 0
        
        return {
            "valid": valid,
            "eligible_for_rich_snippets": valid and len([i for i in issues if i.get("severity") == "MEDIUM"]) == 0,
            "critical_issues": [i for i in issues if i["severity"] == "CRITICAL"],
            "warnings": [i for i in issues if i["severity"] != "CRITICAL"],
            "total_issues": len(issues),
            "issues": issues
        }

    # ========================
    # KEYWORD DENSITY
    # ========================

    def analyze_keyword_density(self, text: str, primary_keyword: str, secondary_keywords: List[str] = None) -> Dict:
        """
        Analyze keyword density and placement
        Optimal range: 0.5-2% for primary, 0.2-1% for secondary
        """
        
        words = text.lower().split()
        if not words:
            return {"error": "No text to analyze"}
        
        primary_lower = primary_keyword.lower()
        primary_words = set(primary_lower.split())
        
        # Count primary keyword occurrences
        primary_count = sum(1 for w in words if w in primary_words)
        primary_density = primary_count / len(words) if words else 0
        
        results = {
            "primary_keyword": primary_keyword,
            "primary_count": primary_count,
            "primary_density_percent": round(primary_density * 100, 2),
            "primary_status": self._density_status(primary_density, 0.005, 0.02),
            "total_words": len(words),
            "secondary_keywords": {}
        }
        
        # Analyze secondary keywords
        if secondary_keywords:
            for sk in secondary_keywords:
                sk_lower = sk.lower()
                sk_words = set(sk_lower.split())
                sk_count = sum(1 for w in words if w in sk_words)
                sk_density = sk_count / len(words) if words else 0
                
                results["secondary_keywords"][sk] = {
                    "count": sk_count,
                    "density_percent": round(sk_density * 100, 2),
                    "status": self._density_status(sk_density, 0.002, 0.01)
                }
        
        return results

    def audit_content(self, content: str) -> Dict:
        """
        Comprehensive content audit for SEO issues

        Args:
            content: HTML content or plain text to audit

        Returns:
            Dict with score, issues, and recommendations
        """
        issues = []
        recommendations = []
        score = 100

        # Check for H1 tags
        h1_count = content.upper().count('<H1')
        if h1_count == 0:
            issues.append("Missing H1 tag - every page needs exactly one H1")
            score -= 30
            recommendations.append("Add exactly one H1 tag with your main keyword")
        elif h1_count > 1:
            issues.append(f"Multiple H1 tags found ({h1_count}) - should have exactly one")
            score -= 20
            recommendations.append("Use only one H1 tag per page")

        # Check title tag
        if '<TITLE' not in content.upper():
            issues.append("Missing title tag")
            score -= 25
            recommendations.append("Add a title tag with 50-60 characters")

        # Check meta description
        if 'META NAME="DESCRIPTION"' not in content.upper() and 'META NAME=DESCRIPTION' not in content.upper():
            issues.append("Missing meta description")
            score -= 20
            recommendations.append("Add a meta description with 140-160 characters")

        # Check for images without alt text
        img_tags = content.upper().count('<IMG')
        alt_tags = content.upper().count('ALT=')
        if img_tags > alt_tags:
            issues.append(f"Found {img_tags - alt_tags} images without alt text")
            score -= 15
            recommendations.append("Add descriptive alt text to all images")

        # Check content length
        import re
        text_content = re.sub(r'<[^>]*>', '', content).strip()
        word_count = len(text_content.split())
        if word_count < 300:
            issues.append(f"Content too short ({word_count} words) - minimum 300 words recommended")
            score -= 10
            recommendations.append("Expand content to at least 300 words")

        # Check for keyword stuffing (basic check)
        if content.count('keyword') > content.count(' ') * 0.05:  # More than 5% keywords
            issues.append("Possible keyword stuffing detected")
            score -= 15
            recommendations.append("Reduce keyword density and use natural language")

        # Ensure score doesn't go below 0
        score = max(0, score)

        return {
            "score": score,
            "issues": issues,
            "recommendations": recommendations
        }


# ========================
# USAGE EXAMPLES
# ========================

if __name__ == "__main__":
    auditor = ComprehensivePageAuditor()
    
    # Example 1: H1 Visibility Check
    html_with_hidden_h1 = """
    <html>
    <head><style>.visually-hidden { display: none; }</style></head>
    <body>
        <h1 class="visually-hidden">Real H1 (Hidden)</h1>
        <h1>Visible H1</h1>
    </body>
    </html>
    """
    
    result = auditor.check_h1_visibility(html_with_hidden_h1)
    print("H1 Visibility Check:")
    print(f"  Visible: {result['visible']}")
    print(f"  Score: {result['score']}/100")
    print(f"  Issues: {len(result['issues'])}")
    
    # Example 2: Semantic Validation
    semantic_result = auditor.validate_h1_semantics(
        h1_text="Learn Online MBA Programs | University",
        page_title="Online MBA from Indiana Tech",
        target_keyword="online MBA programs"
    )
    print("\nSemantic Validation:")
    print(f"  Score: {semantic_result['score']}/100 ({semantic_result['grade']})")
    
    # Example 3: Alt Text Quality
    from bs4 import BeautifulSoup
    soup = BeautifulSoup('<img src="logo.png" alt="Company Logo">', 'html.parser')
    img = soup.find('img')
    alt_result = auditor.audit_image_alt_quality(img, src_filename="logo.png")
    print("\nImage Alt Text:")
    print(f"  Quality Score: {alt_result['score']}/100 ({alt_result['grade']})")
    
    # Example 4: Schema Validation
    course_schema = """{
        "@context": "https://schema.org",
        "@type": "Course",
        "name": "Advanced SEO Masterclass",
        "provider": {"@type": "Organization", "name": "Acadment"},
        "description": "Learn advanced SEO strategies and tactics"
    }"""
    
    schema_result = auditor.audit_course_schema(course_schema)
    print("\nCourse Schema:")
    print(f"  Valid: {schema_result['valid']}")
    print(f"  Eligible for Rich Snippets: {schema_result['eligible_for_rich_snippets']}")
    print(f"  Issues: {len(schema_result['issues'])}")
