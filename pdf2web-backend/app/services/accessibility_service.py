"""Accessibility Service for WCAG compliance and a11y features."""
import re
from typing import List, Dict, Any, Optional
from enum import Enum
from loguru import logger
from pydantic import BaseModel

from app.config import settings


class WCAGLevel(str, Enum):
    """WCAG compliance levels."""
    A = "A"
    AA = "AA"
    AAA = "AAA"


class AccessibilityIssue(BaseModel):
    """Accessibility issue found during validation."""
    rule_id: str
    severity: str  # error, warning, info
    message: str
    element: Optional[str] = None
    suggestion: Optional[str] = None
    wcag_criteria: Optional[str] = None


class AccessibilityReport(BaseModel):
    """Accessibility validation report."""
    passed: bool
    wcag_level: WCAGLevel
    issues: List[AccessibilityIssue]
    score: float  # 0-100
    summary: Dict[str, int]


class AccessibilityService:
    """Service for accessibility validation and enhancement."""
    
    def __init__(self):
        self.wcag_level = WCAGLevel(settings.wcag_level)
        self._rules = self._load_rules()
    
    def _load_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load accessibility validation rules."""
        return {
            # Images
            "img-alt": {
                "level": WCAGLevel.A,
                "severity": "error",
                "message": "Images must have alt text",
                "wcag": "1.1.1"
            },
            "img-alt-empty": {
                "level": WCAGLevel.A,
                "severity": "warning",
                "message": "Decorative images should have empty alt text",
                "wcag": "1.1.1"
            },
            
            # Headings
            "heading-order": {
                "level": WCAGLevel.A,
                "severity": "warning",
                "message": "Heading levels should not skip",
                "wcag": "1.3.1"
            },
            "page-has-h1": {
                "level": WCAGLevel.A,
                "severity": "warning",
                "message": "Page should have exactly one h1",
                "wcag": "1.3.1"
            },
            
            # Links
            "link-name": {
                "level": WCAGLevel.A,
                "severity": "error",
                "message": "Links must have discernible text",
                "wcag": "2.4.4"
            },
            "link-in-text-block": {
                "level": WCAGLevel.A,
                "severity": "warning",
                "message": "Links in text should be distinguishable",
                "wcag": "1.4.1"
            },
            
            # Color contrast
            "color-contrast": {
                "level": WCAGLevel.AA,
                "severity": "error",
                "message": "Text must have sufficient color contrast",
                "wcag": "1.4.3"
            },
            "color-contrast-enhanced": {
                "level": WCAGLevel.AAA,
                "severity": "warning",
                "message": "Text should have enhanced color contrast",
                "wcag": "1.4.6"
            },
            
            # Forms
            "label": {
                "level": WCAGLevel.A,
                "severity": "error",
                "message": "Form inputs must have labels",
                "wcag": "1.3.1"
            },
            
            # Tables
            "table-header": {
                "level": WCAGLevel.A,
                "severity": "error",
                "message": "Tables must have headers",
                "wcag": "1.3.1"
            },
            "table-caption": {
                "level": WCAGLevel.A,
                "severity": "warning",
                "message": "Tables should have captions",
                "wcag": "1.3.1"
            },
            
            # Language
            "html-lang": {
                "level": WCAGLevel.A,
                "severity": "error",
                "message": "HTML must have lang attribute",
                "wcag": "3.1.1"
            },
            
            # Focus
            "focus-visible": {
                "level": WCAGLevel.AA,
                "severity": "warning",
                "message": "Focus indicators should be visible",
                "wcag": "2.4.7"
            },
            
            # ARIA
            "aria-valid": {
                "level": WCAGLevel.A,
                "severity": "error",
                "message": "ARIA attributes must be valid",
                "wcag": "4.1.2"
            }
        }
    
    async def validate_html(self, html: str) -> AccessibilityReport:
        """
        Validate HTML for accessibility issues.
        
        Args:
            html: HTML content to validate
            
        Returns:
            AccessibilityReport with issues found
        """
        issues = []
        
        # Run all applicable rules
        issues.extend(self._check_images(html))
        issues.extend(self._check_headings(html))
        issues.extend(self._check_links(html))
        issues.extend(self._check_tables(html))
        issues.extend(self._check_language(html))
        issues.extend(self._check_forms(html))
        issues.extend(self._check_aria(html))
        
        # Filter by WCAG level
        filtered_issues = [
            i for i in issues 
            if self._rule_applies(i.rule_id)
        ]
        
        # Calculate score
        error_count = sum(1 for i in filtered_issues if i.severity == "error")
        warning_count = sum(1 for i in filtered_issues if i.severity == "warning")
        score = max(0, 100 - (error_count * 10) - (warning_count * 2))
        
        return AccessibilityReport(
            passed=error_count == 0,
            wcag_level=self.wcag_level,
            issues=filtered_issues,
            score=score,
            summary={
                "errors": error_count,
                "warnings": warning_count,
                "info": sum(1 for i in filtered_issues if i.severity == "info")
            }
        )
    
    def _rule_applies(self, rule_id: str) -> bool:
        """Check if rule applies to current WCAG level."""
        rule = self._rules.get(rule_id, {})
        rule_level = rule.get("level", WCAGLevel.A)
        
        level_order = [WCAGLevel.A, WCAGLevel.AA, WCAGLevel.AAA]
        return level_order.index(rule_level) <= level_order.index(self.wcag_level)
    
    def _check_images(self, html: str) -> List[AccessibilityIssue]:
        """Check image accessibility."""
        issues = []
        
        # Find images without alt
        img_pattern = r'<img[^>]*>'
        for match in re.finditer(img_pattern, html, re.IGNORECASE):
            img_tag = match.group()
            if 'alt=' not in img_tag.lower():
                issues.append(AccessibilityIssue(
                    rule_id="img-alt",
                    severity="error",
                    message="Image missing alt attribute",
                    element=img_tag[:100],
                    suggestion="Add alt='description' or alt='' for decorative images",
                    wcag_criteria="1.1.1"
                ))
        
        return issues
    
    def _check_headings(self, html: str) -> List[AccessibilityIssue]:
        """Check heading structure."""
        issues = []
        
        # Find all headings
        heading_pattern = r'<h([1-6])[^>]*>'
        headings = [(int(m.group(1)), m.start()) for m in re.finditer(heading_pattern, html, re.IGNORECASE)]
        
        # Check for h1
        h1_count = sum(1 for h in headings if h[0] == 1)
        if h1_count == 0:
            issues.append(AccessibilityIssue(
                rule_id="page-has-h1",
                severity="warning",
                message="Page should have an h1 heading",
                suggestion="Add an h1 element as the main page heading"
            ))
        elif h1_count > 1:
            issues.append(AccessibilityIssue(
                rule_id="page-has-h1",
                severity="warning",
                message=f"Page has {h1_count} h1 headings, should have exactly one",
                suggestion="Use only one h1 for the main page heading"
            ))
        
        # Check heading order
        prev_level = 0
        for level, pos in headings:
            if level > prev_level + 1 and prev_level > 0:
                issues.append(AccessibilityIssue(
                    rule_id="heading-order",
                    severity="warning",
                    message=f"Heading level skipped from h{prev_level} to h{level}",
                    suggestion=f"Use h{prev_level + 1} instead of h{level}"
                ))
            prev_level = level
        
        return issues
    
    def _check_links(self, html: str) -> List[AccessibilityIssue]:
        """Check link accessibility."""
        issues = []
        
        # Find links
        link_pattern = r'<a[^>]*>(.*?)</a>'
        for match in re.finditer(link_pattern, html, re.IGNORECASE | re.DOTALL):
            link_text = match.group(1).strip()
            link_tag = match.group(0)
            
            # Check for empty links
            if not link_text and 'aria-label' not in link_tag.lower():
                issues.append(AccessibilityIssue(
                    rule_id="link-name",
                    severity="error",
                    message="Link has no discernible text",
                    element=link_tag[:100],
                    suggestion="Add link text or aria-label attribute"
                ))
            
            # Check for generic link text
            generic_texts = ["click here", "read more", "learn more", "here", "more"]
            if link_text.lower() in generic_texts:
                issues.append(AccessibilityIssue(
                    rule_id="link-name",
                    severity="warning",
                    message=f"Link text '{link_text}' is not descriptive",
                    element=link_tag[:100],
                    suggestion="Use descriptive link text that explains the destination"
                ))
        
        return issues
    
    def _check_tables(self, html: str) -> List[AccessibilityIssue]:
        """Check table accessibility."""
        issues = []
        
        # Find tables
        table_pattern = r'<table[^>]*>(.*?)</table>'
        for match in re.finditer(table_pattern, html, re.IGNORECASE | re.DOTALL):
            table_content = match.group(1)
            
            # Check for headers
            if '<th' not in table_content.lower():
                issues.append(AccessibilityIssue(
                    rule_id="table-header",
                    severity="error",
                    message="Table missing header cells (th)",
                    suggestion="Add th elements for table headers"
                ))
            
            # Check for caption
            if '<caption' not in table_content.lower():
                issues.append(AccessibilityIssue(
                    rule_id="table-caption",
                    severity="warning",
                    message="Table missing caption",
                    suggestion="Add a caption element to describe the table"
                ))
        
        return issues
    
    def _check_language(self, html: str) -> List[AccessibilityIssue]:
        """Check language attributes."""
        issues = []
        
        # Check for html lang attribute
        html_tag_pattern = r'<html[^>]*>'
        match = re.search(html_tag_pattern, html, re.IGNORECASE)
        if match:
            html_tag = match.group()
            if 'lang=' not in html_tag.lower():
                issues.append(AccessibilityIssue(
                    rule_id="html-lang",
                    severity="error",
                    message="HTML element missing lang attribute",
                    suggestion='Add lang="en" (or appropriate language code) to html element'
                ))
        
        return issues
    
    def _check_forms(self, html: str) -> List[AccessibilityIssue]:
        """Check form accessibility."""
        issues = []
        
        # Find inputs without labels
        input_pattern = r'<input[^>]*>'
        for match in re.finditer(input_pattern, html, re.IGNORECASE):
            input_tag = match.group()
            
            # Skip hidden and submit inputs
            if 'type="hidden"' in input_tag.lower() or 'type="submit"' in input_tag.lower():
                continue
            
            # Check for id to match with label
            id_match = re.search(r'id=["\']([^"\']+)["\']', input_tag)
            if id_match:
                input_id = id_match.group(1)
                label_pattern = f'<label[^>]*for=["\']?{input_id}["\']?'
                if not re.search(label_pattern, html, re.IGNORECASE):
                    # Check for aria-label
                    if 'aria-label' not in input_tag.lower() and 'aria-labelledby' not in input_tag.lower():
                        issues.append(AccessibilityIssue(
                            rule_id="label",
                            severity="error",
                            message=f"Input '{input_id}' has no associated label",
                            element=input_tag[:100],
                            suggestion="Add a label element with for attribute or aria-label"
                        ))
        
        return issues
    
    def _check_aria(self, html: str) -> List[AccessibilityIssue]:
        """Check ARIA usage."""
        issues = []
        
        # Check for invalid ARIA roles
        valid_roles = [
            "alert", "alertdialog", "application", "article", "banner", "button",
            "cell", "checkbox", "columnheader", "combobox", "complementary",
            "contentinfo", "definition", "dialog", "directory", "document",
            "feed", "figure", "form", "grid", "gridcell", "group", "heading",
            "img", "link", "list", "listbox", "listitem", "log", "main",
            "marquee", "math", "menu", "menubar", "menuitem", "menuitemcheckbox",
            "menuitemradio", "navigation", "none", "note", "option", "presentation",
            "progressbar", "radio", "radiogroup", "region", "row", "rowgroup",
            "rowheader", "scrollbar", "search", "searchbox", "separator", "slider",
            "spinbutton", "status", "switch", "tab", "table", "tablist", "tabpanel",
            "term", "textbox", "timer", "toolbar", "tooltip", "tree", "treegrid", "treeitem"
        ]
        
        role_pattern = r'role=["\']([^"\']+)["\']'
        for match in re.finditer(role_pattern, html, re.IGNORECASE):
            role = match.group(1).lower()
            if role not in valid_roles:
                issues.append(AccessibilityIssue(
                    rule_id="aria-valid",
                    severity="error",
                    message=f"Invalid ARIA role: '{role}'",
                    suggestion=f"Use a valid ARIA role from the specification"
                ))
        
        return issues
    
    async def enhance_html(self, html: str) -> str:
        """
        Enhance HTML with accessibility features.
        
        Args:
            html: HTML content to enhance
            
        Returns:
            Enhanced HTML with accessibility improvements
        """
        enhanced = html
        
        # Add lang attribute if missing
        if '<html' in enhanced and 'lang=' not in enhanced[:200].lower():
            enhanced = enhanced.replace('<html', f'<html lang="{settings.default_language}"', 1)
        
        # Add skip link if enabled
        if settings.enable_skip_links and '<body' in enhanced:
            skip_link = '''
            <a href="#main-content" class="skip-link">Skip to main content</a>
            <style>.skip-link{position:absolute;top:-40px;left:0;background:#000;color:#fff;padding:8px;z-index:100;}.skip-link:focus{top:0;}</style>
            '''
            enhanced = enhanced.replace('<body', f'{skip_link}<body', 1)
            
            # Add main content id if not present
            if 'id="main-content"' not in enhanced:
                enhanced = enhanced.replace('<div class="container">', '<div class="container" id="main-content">', 1)
        
        # Add ARIA labels if enabled
        if settings.auto_aria_labels:
            enhanced = self._add_aria_labels(enhanced)
        
        # Add keyboard navigation styles if enabled
        if settings.keyboard_navigation:
            focus_styles = '''
            <style>
            :focus{outline:2px solid #4e79a7;outline-offset:2px;}
            :focus:not(:focus-visible){outline:none;}
            :focus-visible{outline:2px solid #4e79a7;outline-offset:2px;}
            </style>
            '''
            enhanced = enhanced.replace('</head>', f'{focus_styles}</head>')
        
        # Add high contrast support if enabled
        if settings.support_high_contrast:
            contrast_styles = '''
            <style>
            @media (prefers-contrast: high) {
                body{background:#000!important;color:#fff!important;}
                a{color:#ffff00!important;}
                button,.btn{border:2px solid #fff!important;}
            }
            </style>
            '''
            enhanced = enhanced.replace('</head>', f'{contrast_styles}</head>')
        
        return enhanced
    
    def _add_aria_labels(self, html: str) -> str:
        """Add ARIA labels to elements."""
        enhanced = html
        
        # Add aria-label to navigation
        enhanced = re.sub(
            r'<nav([^>]*)>',
            r'<nav\1 aria-label="Main navigation">',
            enhanced,
            flags=re.IGNORECASE
        )
        
        # Add role to main content
        if '<main' not in enhanced.lower():
            enhanced = enhanced.replace(
                '<div class="container"',
                '<main role="main" class="container"'
            )
            enhanced = enhanced.replace('</div>\n</body>', '</main>\n</body>')
        
        return enhanced


# Singleton instance
accessibility_service = AccessibilityService()
