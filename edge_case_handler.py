"""
Edge Case Handling - Production-Grade Input Sanitization & Output Formatting
Handles XSS prevention, character encoding, SERP truncation, etc.

Key Features:
- HTML/JavaScript XSS prevention
- Special character encoding
- SERP preview truncation
- Character count enforcement
- JSON injection prevention
- URL encoding
- Email validation
"""

import html
import json
import re
import unicodedata
from typing import Optional, Dict, List
from urllib.parse import quote, unquote
import logging

logger = logging.getLogger(__name__)


class EdgeCaseHandler:
    """Production-grade edge case handling"""
    
    # XSS pattern detection
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'on\w+\s*=',  # onclick, onload, etc.
        r'javascript:',
        r'<iframe[^>]*>',
        r'<embed[^>]*>',
        r'<object[^>]*>',
    ]
    
    # SQL injection patterns
    SQL_PATTERNS = [
        r"('\s*(?:union|select|insert|update|delete|drop))",
        r"(;.*--)",
        r"(1'\s*or\s*'1'=?'1')",
    ]

    @staticmethod
    def sanitize_html_input(user_input: str, max_length: int = 5000) -> str:
        """
        Sanitize HTML input for XSS prevention
        
        Args:
            user_input: Raw user input
            max_length: Maximum allowed length
        
        Returns:
            Sanitized, safe string
        """
        
        if not user_input:
            return ""
        
        # Length check
        if len(user_input) > max_length:
            logger.warning(f"⚠️ Input exceeded max length: {len(user_input)} > {max_length}")
            user_input = user_input[:max_length]
        
        # Remove null bytes
        user_input = user_input.replace('\x00', '')
        
        # HTML escape (converts < > & " ' to entities)
        sanitized = html.escape(user_input)
        
        # Remove script tags (even if escaped)
        sanitized = re.sub(r'%3Cscript[^%]*%3E.*?%3C/script%3E', '', sanitized, flags=re.IGNORECASE)
        
        # Remove event handlers (even if escaped)
        sanitized = re.sub(r'%20on\w+%20%3D', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized

    @staticmethod
    def sanitize_text_input(user_input: str, max_length: int = 1000) -> str:
        """
        Sanitize plain text input (no HTML needed)
        
        Args:
            user_input: Raw text input
            max_length: Maximum allowed length
        
        Returns:
            Sanitized text
        """
        
        if not user_input:
            return ""
        
        # Remove null bytes
        user_input = user_input.replace('\x00', '')
        
        # Remove control characters (except newlines, tabs)
        user_input = ''.join(
            char for char in user_input 
            if unicodedata.category(char)[0] != 'C' or char in '\n\t'
        )
        
        # Trim length
        if len(user_input) > max_length:
            logger.warning(f"⚠️ Input exceeded max length: {len(user_input)} > {max_length}")
            user_input = user_input[:max_length]
        
        # Remove extra whitespace
        user_input = re.sub(r'\s+', ' ', user_input).strip()
        
        return user_input

    @staticmethod
    def sanitize_json_input(user_input: str) -> Dict:
        """
        Parse JSON input safely, preventing JSON injection
        
        Args:
            user_input: JSON string
        
        Returns:
            Parsed dictionary, or empty dict if invalid
        """
        
        if not user_input:
            return {}
        
        try:
            # Attempt parse
            data = json.loads(user_input)
            
            # Validate it's a dict (not array or primitive)
            if not isinstance(data, dict):
                logger.warning(f"⚠️ JSON input not a dict: {type(data)}")
                return {}
            
            # Recursively sanitize all string values
            def sanitize_dict(d):
                result = {}
                for key, value in d.items():
                    # Sanitize keys (should be alphanumeric)
                    if not re.match(r'^[a-zA-Z0-9_-]+$', str(key)):
                        logger.warning(f"⚠️ Suspicious JSON key: {key}")
                        continue
                    
                    # Sanitize values
                    if isinstance(value, str):
                        result[key] = EdgeCaseHandler.sanitize_text_input(value)
                    elif isinstance(value, dict):
                        result[key] = sanitize_dict(value)
                    elif isinstance(value, list):
                        result[key] = [EdgeCaseHandler.sanitize_text_input(str(v)) if isinstance(v, str) else v for v in value]
                    else:
                        result[key] = value
                
                return result
            
            return sanitize_dict(data)
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON: {e}")
            return {}

    @staticmethod
    def check_sql_injection(user_input: str) -> Dict:
        """
        Detect potential SQL injection patterns
        
        Returns:
        {
            "safe": bool,
            "patterns_found": List[str],
            "risk_level": "SAFE" | "MEDIUM" | "HIGH"
        }
        """
        
        if not user_input:
            return {"safe": True, "patterns_found": [], "risk_level": "SAFE"}
        
        patterns_found = []
        
        for pattern in EdgeCaseHandler.SQL_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                patterns_found.append(pattern)
        
        if patterns_found:
            logger.warning(f"⚠️ Potential SQL injection detected: {patterns_found}")
        
        return {
            "safe": len(patterns_found) == 0,
            "patterns_found": patterns_found,
            "risk_level": "HIGH" if len(patterns_found) > 1 else ("MEDIUM" if patterns_found else "SAFE")
        }

    @staticmethod
    def check_xss_injection(user_input: str) -> Dict:
        """
        Detect potential XSS injection patterns
        
        Returns:
        {
            "safe": bool,
            "patterns_found": List[str],
            "risk_level": "SAFE" | "MEDIUM" | "HIGH"
        }
        """
        
        if not user_input:
            return {"safe": True, "patterns_found": [], "risk_level": "SAFE"}
        
        patterns_found = []
        
        for pattern in EdgeCaseHandler.XSS_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                patterns_found.append(pattern)
        
        # Also check URL-encoded XSS
        if '%3C' in user_input or '%3E' in user_input:
            patterns_found.append("URL-encoded HTML tags")
        
        if patterns_found:
            logger.warning(f"⚠️ Potential XSS detected: {patterns_found}")
        
        return {
            "safe": len(patterns_found) == 0,
            "patterns_found": patterns_found,
            "risk_level": "HIGH" if len(patterns_found) > 1 else ("MEDIUM" if patterns_found else "SAFE")
        }

    # ========================
    # SERP PREVIEW
    # ========================

    @staticmethod
    def generate_serp_preview(title: str, description: str, url: str) -> Dict:
        """
        Generate SERP preview showing how content appears in search results
        
        Returns:
        {
            "title": "Truncated title for SERP",
            "description": "Truncated description for SERP",
            "url": "Truncated URL for SERP",
            "title_truncated": bool,
            "description_truncated": bool,
            "preview_html": str
        }
        """
        
        # SERP truncation limits (approximations)
        # Desktop: ~60 chars for title, ~160 for description
        # Mobile: ~30 chars for title, ~120 for description
        
        desktop_title_limit = 60
        desktop_desc_limit = 160
        mobile_title_limit = 30
        mobile_desc_limit = 120
        
        # Desktop preview
        desktop_title = title[:desktop_title_limit]
        if len(title) > desktop_title_limit:
            desktop_title = title[:desktop_title_limit - 1] + '…'
        
        desktop_desc = description[:desktop_desc_limit]
        if len(description) > desktop_desc_limit:
            desktop_desc = description[:desktop_desc_limit - 1] + '…'
        
        # Mobile preview
        mobile_title = title[:mobile_title_limit]
        if len(title) > mobile_title_limit:
            mobile_title = title[:mobile_title_limit - 1] + '…'
        
        mobile_desc = description[:mobile_desc_limit]
        if len(description) > mobile_desc_limit:
            mobile_desc = description[:mobile_desc_limit - 1] + '…'
        
        # Truncated URL (typically just domain + path)
        if len(url) > 50:
            url_preview = url[:47] + '…'
        else:
            url_preview = url
        
        return {
            "desktop": {
                "title": desktop_title,
                "description": desktop_desc,
                "title_char_count": len(desktop_title),
                "description_char_count": len(desktop_desc),
            },
            "mobile": {
                "title": mobile_title,
                "description": mobile_desc,
                "title_char_count": len(mobile_title),
                "description_char_count": len(mobile_desc),
            },
            "url": url_preview,
            "warnings": EdgeCaseHandler._get_serp_warnings(title, description)
        }

    @staticmethod
    def _get_serp_warnings(title: str, description: str) -> List[str]:
        """Generate warnings about SERP appearance"""
        
        warnings = []
        
        if len(title) < 30:
            warnings.append("⚠️ Title too short (<30 chars) — may look sparse in SERP")
        elif len(title) > 70:
            warnings.append("⚠️ Title will be truncated in SERP (>70 chars)")
        
        if len(description) < 120:
            warnings.append("⚠️ Description short (<120 chars) — less space for CTA")
        elif len(description) > 170:
            warnings.append("⚠️ Description will be truncated in SERP (>170 chars)")
        
        if not any(char in title for char in ['|', '-', '•']):
            warnings.append("💡 Consider using separator (|, -, •) to break up title")
        
        return warnings

    # ========================
    # CHARACTER ENCODING
    # ========================

    @staticmethod
    def handle_special_characters(text: str) -> str:
        """
        Handle emoji, accents, and special characters
        
        Returns normalized UTF-8 string
        """
        
        if not text:
            return ""
        
        # Normalize unicode (decompose accents)
        text = unicodedata.normalize('NFKD', text)
        
        # Remove emoji (if needed for compatibility)
        # Uncomment to strip emoji:
        # text = text.encode('ascii', 'ignore').decode('ascii')
        
        return text

    @staticmethod
    def url_encode_safe(text: str) -> str:
        """URL-encode text safely"""
        
        if not text:
            return ""
        
        return quote(text, safe='')

    @staticmethod
    def email_validation(email: str) -> Dict:
        """
        Validate email address format
        
        Returns:
        {
            "valid": bool,
            "email": str,
            "reason": Optional[str]
        }
        """
        
        if not email:
            return {"valid": False, "email": email, "reason": "Empty email"}
        
        # RFC 5322 simplified regex (not perfect but catches 99% of invalid)
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if len(email) > 254:
            return {"valid": False, "email": email, "reason": "Email too long (>254 chars)"}
        
        if re.match(email_regex, email):
            return {"valid": True, "email": email.lower(), "reason": None}
        else:
            return {"valid": False, "email": email, "reason": "Invalid email format"}

    # ========================
    # CONTENT VALIDATION
    # ========================

    @staticmethod
    def validate_content_length(
        title: str,
        description: str,
        min_title: int = 30,
        max_title: int = 70,
        min_desc: int = 120,
        max_desc: int = 170
    ) -> Dict:
        """
        Validate content meets length requirements
        
        Returns:
        {
            "title_valid": bool,
            "description_valid": bool,
            "title_issues": [...],
            "description_issues": [...]
        }
        """
        
        title_issues = []
        desc_issues = []
        
        # Title validation
        if len(title) < min_title:
            title_issues.append(f"Too short ({len(title)} chars, min {min_title})")
        if len(title) > max_title:
            title_issues.append(f"Too long ({len(title)} chars, max {max_title})")
        
        # Description validation
        if len(description) < min_desc:
            desc_issues.append(f"Too short ({len(description)} chars, min {min_desc})")
        if len(description) > max_desc:
            desc_issues.append(f"Too long ({len(description)} chars, max {max_desc})")
        
        return {
            "title_valid": len(title_issues) == 0,
            "description_valid": len(desc_issues) == 0,
            "title_issues": title_issues,
            "description_issues": desc_issues,
            "all_valid": len(title_issues) == 0 and len(desc_issues) == 0
        }


# ========================
# USAGE EXAMPLES
# ========================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    handler = EdgeCaseHandler()
    
    print("=" * 60)
    print("EDGE CASE HANDLING EXAMPLES")
    print("=" * 60)
    
    # Example 1: XSS detection
    print("\n1. XSS DETECTION")
    print("-" * 60)
    
    xss_inputs = [
        "Normal text",
        "<script>alert('xss')</script>",
        "javascript:void(0)",
        "<img src=x onerror=alert('xss')>"
    ]
    
    for inp in xss_inputs:
        result = handler.check_xss_injection(inp)
        status = "✅ SAFE" if result['safe'] else "🔴 UNSAFE"
        print(f"{status}: {inp[:50]}")
    
    # Example 2: SQL injection detection
    print("\n2. SQL INJECTION DETECTION")
    print("-" * 60)
    
    sql_inputs = [
        "Normal text",
        "' OR '1'='1",
        "1; DROP TABLE users;--"
    ]
    
    for inp in sql_inputs:
        result = handler.check_sql_injection(inp)
        status = "✅ SAFE" if result['safe'] else "🔴 UNSAFE"
        print(f"{status}: {inp}")
    
    # Example 3: SERP preview
    print("\n3. SERP PREVIEW GENERATION")
    print("-" * 60)
    
    title = "Learn Online MBA Programs | Digital Marketing Certification - Get Started Today"
    desc = "Master digital marketing with our comprehensive online MBA. Get industry certification, flexible scheduling, and career support. Enroll now and transform your career."
    url = "https://example.com/programs/online-mba-digital-marketing"
    
    preview = handler.generate_serp_preview(title, desc, url)
    
    print("DESKTOP VIEW:")
    print(f"  Title ({len(preview['desktop']['title'])} chars): {preview['desktop']['title']}")
    print(f"  Desc ({len(preview['desktop']['description'])} chars): {preview['desktop']['description'][:60]}...")
    
    print("\nMOBILE VIEW:")
    print(f"  Title ({len(preview['mobile']['title'])} chars): {preview['mobile']['title']}")
    print(f"  Desc ({len(preview['mobile']['description'])} chars): {preview['mobile']['description'][:60]}...")
    
    # Example 4: Email validation
    print("\n4. EMAIL VALIDATION")
    print("-" * 60)
    
    emails = ["user@example.com", "invalid.email", "user@domain"]
    for email in emails:
        result = handler.email_validation(email)
        status = "✅ VALID" if result['valid'] else "❌ INVALID"
        print(f"{status}: {email}")
    
    # Example 5: Content length validation
    print("\n5. CONTENT LENGTH VALIDATION")
    print("-" * 60)
    
    validation = handler.validate_content_length(
        title="Short",
        description="Very long description that needs a lot more content to meet minimum requirements for good SERP appearance and user engagement"
    )
    
    print(f"Title valid: {validation['title_valid']}")
    if validation['title_issues']:
        print(f"  Issues: {', '.join(validation['title_issues'])}")
    
    print(f"Description valid: {validation['description_valid']}")
    if validation['description_issues']:
        print(f"  Issues: {', '.join(validation['description_issues'])}")
