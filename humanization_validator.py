"""
Humanization Validator - Production-Grade Implementation
Validates generated SEO content against humanization criteria (0-100 scale)

Key Features:
- Keyword naturalness scoring
- Sentiment & warmth analysis
- Specificity detection
- CTA effectiveness evaluation
- Conversational tone measurement
- Robotic language detection
- Actionable feedback generation
"""

import re
from typing import Dict, List
from collections import Counter


class HumanizationValidator:
    """Validate generated content is truly humanized, not bot-generated"""
    
    def __init__(self):
        # Warmth indicators (benefit-driven language)
        self.warmth_indicators = [
            "you", "your", "earn", "master", "gain", "success",
            "career", "opportunity", "benefit", "flexibility", "achieve",
            "growth", "advance", "improve", "transform", "empower",
            "excel", "thrive", "accomplish", "excel", "unlock",
            "professional", "confidence", "expertise", "skill"
        ]
        
        # Conversational indicators (natural speech patterns)
        self.conversational_indicators = [
            "learn", "explore", "discover", "expert", "support",
            "personalized", "community", "mentor", "hands-on", "real-world",
            "practical", "proven", "trusted", "guided", "authentic",
            "dedicated", "passionate", "experienced", "knowledgeable"
        ]
        
        # Robotic language (corporate template speak)
        self.robotic_indicators = [
            "the program", "students will", "information", "system",
            "requirements", "feature", "includes", "provide", "offer",
            "data", "algorithm", "process", "methodology", "framework",
            "module", "component", "solution", "implement", "execute"
        ]
        
        # Generic/weak terms (avoid these)
        self.generic_terms = [
            "great", "good", "nice", "awesome", "excellent",
            "many", "several", "some", "quite", "very",
            "improve", "help", "support", "enhance", "optimize",
            "best", "top", "leading", "innovative", "cutting-edge"
        ]

    def validate_metadata(self, title: str, description: str, keyword: str) -> Dict:
        """
        Comprehensive humanization score for metadata (0-100)
        
        Returns:
        {
            "overall_score": 0-100,
            "grade": "A+"|"A"|"B"|"C"|"F",
            "breakdown": {check_name: score, ...},
            "feedback": ["feedback string", ...],
            "passed_validation": bool,
            "recommendation": "APPROVED"|"REVIEW NEEDED"|"REJECT - REWORK"
        }
        """
        
        combined_text = f"{title} {description}".lower()
        
        # Perform all validation checks
        checks = {
            "keyword_naturalness": self._check_keyword_density(combined_text, keyword),
            "sentiment_warmth": self._check_sentiment_warmth(combined_text),
            "specificity": self._check_specificity(combined_text),
            "cta_strength": self._check_cta_effectiveness(title + " " + description),
            "conversational_tone": self._check_conversational_tone(combined_text),
            "avoids_robotic_language": self._check_avoids_robotic(combined_text)
        }
        
        # Weighted score calculation
        weights = {
            "keyword_naturalness": 0.20,
            "sentiment_warmth": 0.15,
            "specificity": 0.20,
            "cta_strength": 0.15,
            "conversational_tone": 0.20,
            "avoids_robotic_language": 0.10
        }
        
        total_score = sum(checks[key] * weights[key] for key in checks)
        
        # Grade assignment
        if total_score >= 90:
            grade = "A+"
        elif total_score >= 80:
            grade = "A"
        elif total_score >= 70:
            grade = "B"
        elif total_score >= 60:
            grade = "C"
        else:
            grade = "F"
        
        # Generate feedback
        feedback = self._generate_feedback(checks, title, description)
        
        return {
            "overall_score": int(total_score),
            "grade": grade,
            "breakdown": {k: int(v) for k, v in checks.items()},
            "feedback": feedback,
            "passed_validation": total_score >= 70,
            "recommendation": (
                "APPROVED" if total_score >= 80 
                else "REVIEW NEEDED" if total_score >= 70 
                else "REJECT - REWORK"
            ),
            "checks_detail": checks
        }

    def validate_full_content(self, h1: str, headers: List[str], paragraphs: List[str], ctas: List[str]) -> Dict:
        """
        Validate humanization across full page content
        
        Returns comprehensive report with per-section scores
        """
        
        all_text = " ".join([h1] + headers + paragraphs + ctas).lower()
        
        sections = {
            "h1": h1,
            "headers": " ".join(headers),
            "paragraphs": " ".join(paragraphs),
            "ctas": " ".join(ctas)
        }
        
        section_scores = {}
        for section_name, section_text in sections.items():
            section_scores[section_name] = {
                "warmth": self._check_sentiment_warmth(section_text.lower()),
                "specificity": self._check_specificity(section_text.lower()),
                "conversational": self._check_conversational_tone(section_text.lower()),
                "robotic": self._check_avoids_robotic(section_text.lower())
            }
        
        # Overall assessment
        overall_warmth = self._check_sentiment_warmth(all_text)
        overall_specificity = self._check_specificity(all_text)
        overall_conversational = self._check_conversational_tone(all_text)
        overall_robotic = self._check_avoids_robotic(all_text)
        
        overall_score = (
            overall_warmth * 0.25 +
            overall_specificity * 0.25 +
            overall_conversational * 0.25 +
            overall_robotic * 0.25
        )
        
        issues = []
        if overall_warmth < 70:
            issues.append("❤️ WARMTH: Add benefit-focused language (earn, master, advance)")
        if overall_specificity < 70:
            issues.append("📊 SPECIFICITY: Use concrete numbers/names instead of generic claims")
        if overall_conversational < 70:
            issues.append("💬 TONE: Write conversationally; use 'you/your'; avoid corporate speak")
        if overall_robotic > 30:
            issues.append("🤖 ROBOTIC: Replace template language with natural speech")
        
        return {
            "overall_score": int(overall_score),
            "section_scores": section_scores,
            "issues": issues,
            "passed": overall_score >= 70,
            "recommendation": "APPROVED" if overall_score >= 80 else "REVIEW NEEDED" if overall_score >= 70 else "REWORK"
        }

    # ========================
    # VALIDATION CHECKS
    # ========================

    def _check_keyword_density(self, text: str, keyword: str) -> float:
        """
        Score 0-100: Is keyword density natural? (0.5-2% optimal)
        """
        
        words = text.split()
        keyword_words = keyword.lower().split()
        keyword_count = sum(1 for w in words if w in keyword_words)
        
        if not words:
            return 0
        
        density = keyword_count / len(words)
        
        # Optimal: 0.5-2%
        if 0.005 <= density <= 0.02:
            return 100
        elif 0.002 <= density < 0.005:  # Underutilized
            return 70
        elif 0.02 < density <= 0.04:  # Slightly over-optimized
            return 70
        else:  # Too sparse or stuffed
            return 30

    def _check_sentiment_warmth(self, text: str) -> float:
        """
        Score 0-100: Does text use warm, benefit-focused language?
        """
        
        warmth_count = sum(1 for indicator in self.warmth_indicators if indicator in text)
        conversational_count = sum(1 for indicator in self.conversational_indicators if indicator in text)
        robotic_count = sum(1 for indicator in self.robotic_indicators if indicator in text)
        
        warmth_score = (warmth_count * 8) + (conversational_count * 5)
        robotic_penalty = robotic_count * 3
        
        return max(0, min(100, warmth_score - robotic_penalty))

    def _check_specificity(self, text: str) -> float:
        """
        Score 0-100: Are claims specific or generic?
        Looks for concrete data: numbers, company names, percentages
        """
        
        generic_count = sum(1 for term in self.generic_terms if f" {term} " in f" {text} ")
        
        # Look for specific data points
        specific_patterns = [
            r'\$\d{2,3}[Kk]',           # Salary: $85K
            r'\d+(?:\.|,)?\d*%',        # Percentage: 95%
            r'\d+(?:\s+)?(?:month|week|day|hour)',  # Duration
            r'(?:Top|Fortune)\s+\d+',   # Fortune 500
            r'[A-Z][a-zA-Z]+ [A-Z][a-zA-Z]+',  # Company names (Title Case)
            r'\b\d{1,2}\+\s+year',      # Experience: 15+ years
        ]
        
        specific_count = sum(1 for pattern in specific_patterns if re.search(pattern, text))
        
        specificity_score = (specific_count * 15) - (generic_count * 5)
        
        return max(0, min(100, specificity_score))

    def _check_cta_effectiveness(self, text: str) -> float:
        """
        Score 0-100: Is CTA clear and compelling?
        """
        
        strong_ctas = [
            "apply now", "enroll today", "start learning", "begin your journey",
            "get started", "join us", "join today", "learn more", "explore programs",
            "claim your spot", "secure enrollment", "register now"
        ]
        
        weak_ctas = ["click here", "learn more"]
        
        text_lower = text.lower()
        
        # Check for strong CTA
        for strong in strong_ctas:
            if strong in text_lower:
                return 100
        
        # Check for weak CTA
        for weak in weak_ctas:
            if weak in text_lower:
                return 50
        
        # No CTA
        return 0

    def _check_conversational_tone(self, text: str) -> float:
        """
        Score 0-100: Is tone conversational (not corporate)?
        """
        
        # Second-person pronouns (you/your) = direct address
        you_pronouns = len(re.findall(r'\byou\b|\byour\b', text, re.IGNORECASE))
        
        # Question marks = engagement
        questions = text.count('?')
        
        # Contractions = casual speech
        contractions = len(re.findall(r"\b\w+n't\b|\b\w+'re\b|\b\w+'s\b", text))
        
        conversational_score = (you_pronouns * 5) + (questions * 8) + (contractions * 3)
        
        return max(0, min(100, conversational_score))

    def _check_avoids_robotic(self, text: str) -> float:
        """
        Score 0-100: Are robotic patterns minimized?
        """
        
        robotic_patterns = [
            r'the program will',
            r'students will (?:be|get|learn)',
            r'we believe that',
            r'at our (?:university|school)',
            r'this course provides',
            r'the main objective',
            r'in conclusion',
            r'as previously mentioned'
        ]
        
        robotic_matches = sum(1 for pattern in robotic_patterns if re.search(pattern, text, re.IGNORECASE))
        
        robotic_score = 100 - (robotic_matches * 15)
        
        return max(0, robotic_score)

    # ========================
    # FEEDBACK GENERATION
    # ========================

    def _generate_feedback(self, checks: Dict, title: str, description: str) -> List[str]:
        """Generate actionable feedback based on check scores"""
        
        feedback = []
        
        if checks["keyword_naturalness"] < 70:
            feedback.append(
                "🔑 KEYWORD: Adjust keyword density. Appears either too sparse or over-optimized. "
                "Target 0.5-2% in your title and description combined."
            )
        
        if checks["sentiment_warmth"] < 70:
            feedback.append(
                "❤️ WARMTH: Add 2-3 benefit-focused phrases. Use words like 'earn', 'master', "
                "'advance', 'career', 'opportunity' to emphasize user benefits."
            )
        
        if checks["specificity"] < 70:
            feedback.append(
                "📊 SPECIFICITY: Replace vague claims with concrete data. "
                "Instead of 'good salary', say '$85K avg salary'. Use percentages, numbers, company names."
            )
        
        if checks["cta_strength"] < 70:
            feedback.append(
                "🎯 CTA: Add clear call-to-action. Use action verbs: "
                "'Apply Now', 'Enroll Today', 'Start Learning', 'Join Now'."
            )
        
        if checks["conversational_tone"] < 70:
            feedback.append(
                "💬 TONE: Write more conversationally. Use 'you/your', ask questions, "
                "use contractions (can't, doesn't). Write like you're talking to a friend."
            )
        
        if checks["avoids_robotic_language"] < 70:
            feedback.append(
                "🤖 ROBOTIC: Avoid template language. Instead of 'the program will teach you', "
                "say 'you'll master'. Replace 'students will learn' with 'you'll discover'."
            )
        
        return feedback

    # ========================
    # BATCH VALIDATION
    # ========================

    def validate_batch(self, content_items: List[Dict]) -> Dict:
        """
        Validate multiple content items and return summary report
        
        content_items: [{"title": str, "description": str, "keyword": str}, ...]
        """
        
        results = []
        total_score = 0
        
        for item in content_items:
            result = self.validate_metadata(
                title=item["title"],
                description=item["description"],
                keyword=item["keyword"]
            )
            results.append({
                "title": item["title"][:50],  # Truncate for display
                "score": result["overall_score"],
                "grade": result["grade"],
                "passed": result["passed_validation"]
            })
            total_score += result["overall_score"]
        
        avg_score = total_score / len(results) if results else 0
        passed_count = sum(1 for r in results if r["passed"])
        
        return {
            "total_items": len(results),
            "average_score": int(avg_score),
            "passed_count": passed_count,
            "failed_count": len(results) - passed_count,
            "pass_rate": f"{(passed_count/len(results)*100):.1f}%" if results else "0%",
            "results": results,
            "summary": f"{passed_count}/{len(results)} items passed validation"
        }


# ========================
# USAGE EXAMPLES
# ========================

if __name__ == "__main__":
    validator = HumanizationValidator()
    
    # Example 1: Metadata validation
    print("=" * 60)
    print("EXAMPLE 1: Metadata Validation")
    print("=" * 60)
    
    result = validator.validate_metadata(
        title="Online MBA from Indiana Tech – Apply Now",
        description="Earn your STEM MBA with OPT benefits. Flexible learning, 100% career support, global alumni. Apply today.",
        keyword="online MBA programs"
    )
    
    print(f"Score: {result['overall_score']}/100 ({result['grade']})")
    print(f"Status: {result['recommendation']}")
    print("\nBreakdown:")
    for check, score in result["breakdown"].items():
        print(f"  {check}: {score}/100")
    print("\nFeedback:")
    for item in result["feedback"]:
        print(f"  {item}")
    
    # Example 2: Full content validation
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Full Content Validation")
    print("=" * 60)
    
    h1 = "Master Digital Marketing in 18 Weeks"
    headers = [
        "What You'll Learn",
        "Why Choose Our Program?",
        "Career Outcomes"
    ]
    paragraphs = [
        "You'll gain hands-on experience with real campaigns. Our expert instructors have 15+ years in the industry.",
        "Flexible online learning means you work at your own pace. 95% of graduates report career advancement."
    ]
    ctas = [
        "Apply now and start your career transformation",
        "Enroll today to secure your spot in the next cohort"
    ]
    
    result2 = validator.validate_full_content(h1, headers, paragraphs, ctas)
    print(f"Overall Score: {result2['overall_score']}/100")
    print(f"Status: {result2['recommendation']}")
    if result2["issues"]:
        print("\nIssues Found:")
        for issue in result2["issues"]:
            print(f"  {issue}")
    
    # Example 3: Batch validation
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Batch Validation")
    print("=" * 60)
    
    batch = [
        {
            "title": "Best Online MBA Programs 2024",
            "description": "Compare top online MBA programs with flexible schedules and career support.",
            "keyword": "online MBA"
        },
        {
            "title": "Learn SEO Online - $2000/Month Avg Salary Increase",
            "description": "Master SEO strategies. 90% of graduates secure high-paying roles. Enroll today.",
            "keyword": "SEO courses"
        }
    ]
    
    batch_result = validator.validate_batch(batch)
    print(f"Batch Summary: {batch_result['summary']}")
    print(f"Pass Rate: {batch_result['pass_rate']}")
    print(f"Average Score: {batch_result['average_score']}/100")
