"""ERNIE Cloud Service for semantic analysis and HTML generation.

Supports multimodal (vision) capabilities via Novita AI for enhanced
table/chart detection and visual document analysis.
"""
import base64
import httpx
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models.schemas import (
    ContentBlock, ContentType, SemanticSuggestion, 
    ComponentSuggestion, ThemeAnalysis, ThemeType
)
from app.config import settings


def extract_json_from_response(response: str) -> dict:
    """Extract JSON from a response that may be wrapped in markdown code blocks."""
    if not response:
        return {}
    
    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        # Try to find raw JSON object
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response.strip()
    
    # Handle empty or whitespace-only JSON string
    if not json_str:
        logger.warning(f"Empty JSON string extracted from response: {response[:100]}...")
        return {}
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Try to clean up common issues
        try:
            json_str = json_str.replace('\n', ' ').replace('\r', '')
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from response: {json_str[:200]}... Error: {e}")
            return {}


class ERNIEService:
    """Service for ERNIE/LLM API interactions with multimodal support.
    
    Supports:
    - Text-only analysis (default, cost-effective)
    - Multimodal vision analysis (for PDF page images)
    - Novita AI, OpenRouter, and Baidu ERNIE backends
    """
    
    # ERNIE models available on Novita AI (as of Dec 2025)
    # Check https://novita.ai/model-api/product/llm-api for latest model names
    ERNIE_MODELS = [
        "baidu/ernie-4.5-21B-a3b",           # Recommended - good balance
        "baidu/ernie-4.5-21B-a3b-thinking",  # With reasoning
        "baidu/ernie-4.5-vl-28b-a3b",        # Vision/Multimodal capable
        "baidu/ernie-4.5-vl-28b-a3b-thinking", # Vision + reasoning
        "baidu/ernie-4.5-300b-a47b-paddle",  # Largest, most capable
        "baidu/ernie-4.5-vl-424b-a47b",      # Large vision model
    ]
    
    def __init__(self):
        self.api_url = settings.ernie_api_url
        self.api_key = settings.ernie_api_key
        self.access_token = settings.ernie_access_token
        self.model = settings.ernie_model
        self.max_tokens = settings.ernie_max_tokens
        self.temperature = settings.ernie_temperature
        self._client = None
        
        # Vision model for multimodal analysis
        self.vision_model = settings.ernie_vision_model
        self.enable_vision = settings.enable_vision_analysis
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=settings.ernie_request_timeout)
        return self._client
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def _call_ernie(self, prompt: str, system_prompt: str = None) -> str:
        """Make a call to ERNIE API."""
        # Check for API key (third-party providers) or access token (Baidu direct)
        if not self.api_key and not self.access_token:
            logger.warning("ERNIE credentials not configured, using mock response")
            return self._mock_response(prompt)
        
        headers = {"Content-Type": "application/json"}
        
        # Build URL based on authentication method
        if self.access_token:
            # Baidu direct API
            url = f"{self.api_url}?access_token={self.access_token}"
        else:
            # Third-party API (OpenRouter, etc.) using API key
            url = self.api_url
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Build payload with cost optimization settings
        payload = {
            "messages": messages,
            "model": self.model,  # Use configured model (ernie-3.5-turbo for savings)
            "max_tokens": self.max_tokens,  # Limit output tokens
            "temperature": self.temperature
        }
        
        try:
            logger.debug(f"Calling ERNIE API: {url} with model {self.model}")
            response = await self.client.post(url, json=payload, headers=headers)
            
            # Log response details for debugging
            if response.status_code != 200:
                logger.error(f"ERNIE API error {response.status_code}: {response.text[:500]}")
            
            response.raise_for_status()
            result = response.json()
            
            # Handle both Baidu and OpenAI-compatible response formats
            content = result.get("result", "") or result.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.debug(f"ERNIE API success, response length: {len(content)}")
            return content
        except httpx.HTTPStatusError as e:
            logger.error(f"ERNIE API HTTP error {e.response.status_code}: {e.response.text[:300]}")
            raise
        except Exception as e:
            logger.error(f"ERNIE API call failed: {e}")
            raise
    
    def _mock_response(self, prompt: str) -> str:
        """Provide mock response when ERNIE is not configured or API fails."""
        if "theme" in prompt.lower():
            return '{"theme": "dark", "confidence": 0.85, "reasoning": "Default dark theme applied"}'
        elif "semantic" in prompt.lower() or "component" in prompt.lower():
            return '{"suggestions": []}'
        elif "html" in prompt.lower():
            return "<html><body><p>Mock HTML output</p></body></html>"
        elif "table" in prompt.lower() or "chart" in prompt.lower():
            return '{"tables": [], "charts": [], "quizzes": []}'
        return "Mock response"
    
    async def _call_ernie_safe(self, prompt: str, system_prompt: str = None) -> str:
        """Safe wrapper that falls back to mock on API failure."""
        try:
            return await self._call_ernie(prompt, system_prompt)
        except Exception as e:
            logger.warning(f"ERNIE API failed, using fallback: {e}")
            return self._mock_response(prompt)
    
    async def analyze_page_image(
        self, 
        image_path: Union[str, Path],
        ocr_text: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze a PDF page image using multimodal vision model.
        
        This provides enhanced detection of:
        - Tables suitable for chart conversion
        - Q&A lists for quiz widgets
        - Timeline/chronological data
        - Geographic/location data for maps
        
        Args:
            image_path: Path to the page image (PNG/JPG)
            ocr_text: Optional OCR text for context
            
        Returns:
            Dict with detected components and suggestions
        """
        if not self.api_key:
            logger.warning("API key not configured, using text-only analysis")
            return {"tables": [], "charts": [], "quizzes": [], "timelines": [], "maps": [], "confidence": 0.0}
        
        # Read and encode image
        image_path = Path(image_path)
        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return {"tables": [], "charts": [], "quizzes": [], "timelines": [], "maps": [], "confidence": 0.0}
        
        with open(image_path, "rb") as f:
            img_data = f.read()
            img_base64 = base64.b64encode(img_data).decode()
        
        # Log image info
        img_size_kb = len(img_data) / 1024
        logger.debug(f"Analyzing image: {image_path.name}, size: {img_size_kb:.1f}KB")
        
        # Determine image MIME type
        suffix = image_path.suffix.lower()
        mime_type = "image/png" if suffix == ".png" else "image/jpeg"
        
        # Improved prompt with clearer instructions
        prompt = """Analyze this PDF page image carefully. Identify content that can be converted to interactive web components.

Look for these specific elements:

1. DATA TABLES: Tables with numeric data (sales figures, statistics, percentages, prices)
   - If found, specify chart_type: "bar" for comparisons, "line" for trends over time, "pie" for proportions
   - Include data_summary describing what the data shows
   
2. QUIZ/Q&A CONTENT: Multiple choice questions, true/false questions, numbered questions with answers
   - Count the questions and identify the type
   
3. TIMELINE DATA: Dates, years, chronological events, historical sequences, project milestones
   - Count the number of events/dates
   
4. LOCATION/MAP DATA: Addresses, city names, countries, geographic references
   - Count the locations mentioned

IMPORTANT: Only include items you actually find. If an element is not present, use an empty array [].

Respond with valid JSON:
{
    "tables": [{"chart_type": "bar|line|pie", "data_summary": "description of the data"}],
    "quizzes": [{"question_count": N, "type": "multiple_choice|true_false|open_ended"}],
    "timelines": [{"event_count": N}],
    "maps": [{"location_count": N}],
    "confidence": 0.0-1.0,
    "description": "Brief description of the page content"
}"""

        if ocr_text:
            prompt += f"\n\nExtracted text from this page:\n{ocr_text[:1500]}"
        
        try:
            response = await self._call_vision(prompt, img_base64, mime_type)
            
            # Check for empty or invalid response
            if not response or response.strip() in ['', '```json', '```json\n```', '```\n```']:
                logger.warning(f"Vision API returned empty/invalid response: '{response[:100] if response else 'None'}...'")
                return {"tables": [], "quizzes": [], "timelines": [], "maps": [], "confidence": 0.0}
            
            # Parse JSON from response (may be wrapped in markdown code blocks)
            result = extract_json_from_response(response)
            
            # Validate result structure
            if not isinstance(result, dict):
                logger.warning(f"Vision API returned non-dict: {type(result)}")
                return {"tables": [], "quizzes": [], "timelines": [], "maps": [], "confidence": 0.0}
            
            # Ensure all required keys exist
            result.setdefault("tables", [])
            result.setdefault("quizzes", [])
            result.setdefault("timelines", [])
            result.setdefault("maps", [])
            result.setdefault("confidence", 0.0)
            result.setdefault("description", "")
            
            # Filter out items with count=0 (model sometimes returns these)
            result["quizzes"] = [q for q in result["quizzes"] if q.get("question_count", 0) > 0]
            result["timelines"] = [t for t in result["timelines"] if t.get("event_count", 0) > 0]
            result["maps"] = [m for m in result["maps"] if m.get("location_count", 0) > 0]
            
            logger.info(f"Vision analysis: tables={len(result['tables'])}, quizzes={len(result['quizzes'])}, "
                       f"timelines={len(result['timelines'])}, maps={len(result['maps'])}, "
                       f"confidence={result['confidence']}, desc='{result.get('description', '')[:50]}...'")
            
            return result
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"tables": [], "charts": [], "quizzes": [], "timelines": [], "maps": [], "confidence": 0.0}
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=5))
    async def _call_vision(
        self, 
        prompt: str, 
        image_base64: str,
        mime_type: str = "image/png"
    ) -> str:
        """Make a multimodal vision API call to Novita AI."""
        if not self.api_key:
            return self._mock_response(prompt)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Log image size for debugging
        img_size_kb = len(image_base64) * 3 / 4 / 1024  # Approximate decoded size
        logger.debug(f"Vision API: image size ~{img_size_kb:.1f}KB, model={self.vision_model}")
        
        # Build multimodal message with image
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_base64}"
                    }
                }
            ]
        }]
        
        payload = {
            "model": self.vision_model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.3  # Lower temp for structured output
        }
        
        try:
            logger.debug(f"Calling Vision API: {self.api_url}")
            response = await self.client.post(
                self.api_url, 
                json=payload, 
                headers=headers
            )
            
            # Log full response for debugging
            if response.status_code != 200:
                logger.error(f"Vision API error {response.status_code}: {response.text[:500]}")
            
            response.raise_for_status()
            result = response.json()
            
            # Log raw response for debugging
            logger.debug(f"Vision API raw result: {result}")
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.debug(f"Vision API response: {content}")
            return content
            
        except Exception as e:
            logger.error(f"Vision API call failed: {e}")
            raise
    
    async def analyze_theme(self, markdown: str) -> ThemeAnalysis:
        """Analyze document content to suggest appropriate theme."""
        prompt = f"""Analyze the following document content and suggest the most appropriate visual theme.
        
Document content:
{markdown[:2000]}  # Limit content length

Respond with JSON containing:
- theme: one of "light", "dark", "professional", "academic", "minimal"
- confidence: float between 0 and 1
- reasoning: brief explanation

JSON response:"""
        
        system_prompt = "You are a document analysis assistant. Respond only with valid JSON."
        
        try:
            response = await self._call_ernie(prompt, system_prompt)
            # Parse JSON from response (may be wrapped in markdown code blocks)
            data = extract_json_from_response(response)
            
            return ThemeAnalysis(
                suggested_theme=ThemeType(data.get("theme", "light")),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", "Default theme suggestion")
            )
        except Exception as e:
            logger.error(f"Theme analysis failed: {e}")
            return ThemeAnalysis(
                suggested_theme=ThemeType.LIGHT,
                confidence=0.5,
                reasoning="Default theme due to analysis error"
            )
    
    async def analyze_semantics(
        self, 
        blocks: List[ContentBlock],
        page_images: Optional[Dict[int, str]] = None
    ) -> List[SemanticSuggestion]:
        """Analyze content blocks for semantic component suggestions.
        
        Args:
            blocks: List of content blocks from OCR
            page_images: Optional dict mapping page numbers to image paths
                        for enhanced multimodal analysis
        
        Returns:
            List of semantic suggestions for interactive components
        """
        suggestions = []
        
        logger.debug(f"Analyzing {len(blocks)} blocks, page_images: {len(page_images) if page_images else 0}")
        
        # Log block types for debugging
        block_types = {}
        for b in blocks:
            block_types[b.type.value] = block_types.get(b.type.value, 0) + 1
        logger.debug(f"Block types: {block_types}")
        
        # If page images provided, use vision analysis for enhanced detection
        if page_images and self.api_key and self.enable_vision:
            logger.info(f"Running vision analysis on {len(page_images)} page images")
            vision_suggestions = await self._analyze_with_vision(blocks, page_images)
            suggestions.extend(vision_suggestions)
            logger.info(f"Vision analysis found {len(vision_suggestions)} suggestions")
        
        # Standard text-based analysis
        text_suggestions = 0
        for block in blocks:
            # Skip if already has vision-based suggestion
            if any(s.block_id == block.id for s in suggestions):
                continue
                
            if block.type == ContentType.TABLE:
                suggestion = await self._analyze_table(block)
                if suggestion:
                    suggestions.append(suggestion)
                    text_suggestions += 1
                    
            elif block.type == ContentType.LIST:
                suggestion = await self._analyze_list(block)
                if suggestion:
                    suggestions.append(suggestion)
                    text_suggestions += 1
                    
            elif block.type == ContentType.CODE:
                suggestions.append(SemanticSuggestion(
                    block_id=block.id,
                    suggestion=ComponentSuggestion.CODE_BLOCK,
                    confidence=0.95,
                    config={"language": self._detect_language(block.content)}
                ))
                text_suggestions += 1
            
            # Also check paragraphs for patterns
            elif block.type == ContentType.PARAGRAPH:
                suggestion = await self._analyze_paragraph(block)
                if suggestion:
                    suggestions.append(suggestion)
                    text_suggestions += 1
        
        logger.info(f"Text analysis found {text_suggestions} additional suggestions. Total: {len(suggestions)}")
        
        return suggestions
    
    async def _analyze_paragraph(self, block: ContentBlock) -> Optional[SemanticSuggestion]:
        """Analyze paragraph content for potential interactive components."""
        content = block.content.lower()
        original_content = block.content
        
        # Check for Q&A patterns in paragraphs
        qa_patterns = ["q:", "a:", "question:", "answer:", "?", "a)", "b)", "c)", "d)"]
        qa_count = sum(1 for p in qa_patterns if p in content)
        if qa_count >= 2:
            logger.debug(f"Block {block.id}: Q&A pattern detected (count={qa_count})")
            return SemanticSuggestion(
                block_id=block.id,
                suggestion=ComponentSuggestion.QUIZ,
                confidence=0.7,
                config={"type": "qa_detected", "source": "text_pattern"}
            )
        
        # Check for timeline/date patterns
        date_patterns = [
            r'\b\d{4}\b',  # Years like 2024
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # Dates like 12/25/2024
            r'\b(q1|q2|q3|q4)\b',  # Quarters
        ]
        date_count = sum(len(re.findall(p, content, re.IGNORECASE)) for p in date_patterns)
        if date_count >= 3:
            logger.debug(f"Block {block.id}: Timeline pattern detected (date_count={date_count})")
            return SemanticSuggestion(
                block_id=block.id,
                suggestion=ComponentSuggestion.TIMELINE,
                confidence=0.65,
                config={"date_count": date_count, "source": "text_pattern"}
            )
        
        # Check for numeric data that could be a chart
        numeric_patterns = [
            r'\b\d+(?:\.\d+)?%',  # Percentages like 25%, 3.5%
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?',  # Currency like $1,000.00
            r'\b\d+(?:,\d{3})+\b',  # Large numbers with commas
            r'\b\d+(?:\.\d+)?\s*(?:million|billion|thousand|k|m|b)\b',  # Numbers with units
        ]
        
        # Count significant numeric values
        numbers = []
        for pattern in numeric_patterns:
            numbers.extend(re.findall(pattern, content, re.IGNORECASE))
        
        # If we found formatted numbers, suggest a chart
        if len(numbers) >= 3:
            logger.debug(f"Block {block.id}: Numeric data detected ({len(numbers)} values)")
            return SemanticSuggestion(
                block_id=block.id,
                suggestion=ComponentSuggestion.CHART_BAR,
                confidence=0.7,
                config={"numeric_count": len(numbers), "source": "text_pattern"}
            )
        
        # Check for code-like content
        code_indicators = ["def ", "function ", "class ", "import ", "const ", "var ", "let ", "=>", "return "]
        if any(ind in original_content for ind in code_indicators):
            logger.debug(f"Block {block.id}: Code pattern detected")
            return SemanticSuggestion(
                block_id=block.id,
                suggestion=ComponentSuggestion.CODE_BLOCK,
                confidence=0.75,
                config={"language": self._detect_language(original_content), "source": "text_pattern"}
            )
        
        return None
    
    async def _analyze_with_vision(
        self,
        blocks: List[ContentBlock],
        page_images: Dict[int, str]
    ) -> List[SemanticSuggestion]:
        """Use vision model to analyze page images for better component detection."""
        suggestions = []
        
        for page_num, image_path in page_images.items():
            # Get OCR text for this page
            page_text = "\n".join(
                b.content for b in blocks if b.page == page_num
            )
            
            try:
                result = await self.analyze_page_image(image_path, page_text)
                
                # Convert vision results to semantic suggestions
                # Match detected components to blocks by page
                page_blocks = [b for b in blocks if b.page == page_num]
                
                # Process detected tables → charts
                for table_info in result.get("tables", []):
                    chart_type = table_info.get("chart_type", "bar")
                    # Find matching table block on this page
                    for block in page_blocks:
                        if block.type == ContentType.TABLE:
                            chart_map = {
                                "bar": ComponentSuggestion.CHART_BAR,
                                "line": ComponentSuggestion.CHART_LINE,
                                "pie": ComponentSuggestion.CHART_PIE
                            }
                            suggestions.append(SemanticSuggestion(
                                block_id=block.id,
                                suggestion=chart_map.get(chart_type, ComponentSuggestion.CHART_BAR),
                                confidence=result.get("confidence", 0.8),
                                config={
                                    "source": "vision",
                                    "data_summary": table_info.get("data_summary", "")
                                }
                            ))
                            break
                
                # Process detected quizzes
                for quiz_info in result.get("quizzes", []):
                    for block in page_blocks:
                        if block.type == ContentType.LIST:
                            suggestions.append(SemanticSuggestion(
                                block_id=block.id,
                                suggestion=ComponentSuggestion.QUIZ,
                                confidence=result.get("confidence", 0.8),
                                config={
                                    "source": "vision",
                                    "type": quiz_info.get("type", "multiple_choice"),
                                    "question_count": quiz_info.get("question_count", 1)
                                }
                            ))
                            break
                
                # Process detected timelines
                for timeline_info in result.get("timelines", []):
                    for block in page_blocks:
                        if block.type in [ContentType.LIST, ContentType.PARAGRAPH]:
                            suggestions.append(SemanticSuggestion(
                                block_id=block.id,
                                suggestion=ComponentSuggestion.TIMELINE,
                                confidence=result.get("confidence", 0.75),
                                config={
                                    "source": "vision",
                                    "event_count": timeline_info.get("event_count", 1)
                                }
                            ))
                            break
                
                # Process detected maps
                for map_info in result.get("maps", []):
                    for block in page_blocks:
                        suggestions.append(SemanticSuggestion(
                            block_id=block.id,
                            suggestion=ComponentSuggestion.MAP,
                            confidence=result.get("confidence", 0.75),
                            config={
                                "source": "vision",
                                "location_count": map_info.get("location_count", 1)
                            }
                        ))
                        break
                        
            except Exception as e:
                logger.warning(f"Vision analysis failed for page {page_num}: {e}")
                continue
        
        return suggestions
    
    async def _analyze_table(self, block: ContentBlock) -> Optional[SemanticSuggestion]:
        """Analyze table content for chart suggestions."""
        prompt = f"""Analyze this table data and suggest the best chart type for visualization.

Table content:
{block.content}

Respond with JSON:
- chart_type: "bar", "line", "pie", or "none"
- confidence: float 0-1
- config: chart configuration (labels, data keys, etc.)

JSON response:"""
        
        try:
            response = await self._call_ernie(prompt)
            # Parse JSON from response (may be wrapped in markdown code blocks)
            data = extract_json_from_response(response)
            
            chart_type = data.get("chart_type", "none")
            if chart_type == "none":
                return None
            
            chart_map = {
                "bar": ComponentSuggestion.CHART_BAR,
                "line": ComponentSuggestion.CHART_LINE,
                "pie": ComponentSuggestion.CHART_PIE
            }
            
            return SemanticSuggestion(
                block_id=block.id,
                suggestion=chart_map.get(chart_type, ComponentSuggestion.CHART_BAR),
                confidence=float(data.get("confidence", 0.7)),
                config=data.get("config", {})
            )
        except Exception as e:
            logger.warning(f"Table analysis failed: {e}")
            # Default to bar chart for tables with numeric data
            if any(c.isdigit() for c in block.content):
                return SemanticSuggestion(
                    block_id=block.id,
                    suggestion=ComponentSuggestion.CHART_BAR,
                    confidence=0.6,
                    config={}
                )
            return None
    
    async def _analyze_list(self, block: ContentBlock) -> Optional[SemanticSuggestion]:
        """Analyze list content for quiz suggestions."""
        content_lower = block.content.lower()
        
        # Check for Q&A patterns
        qa_indicators = ["?", "answer:", "a)", "b)", "c)", "correct", "true", "false"]
        if any(indicator in content_lower for indicator in qa_indicators):
            return SemanticSuggestion(
                block_id=block.id,
                suggestion=ComponentSuggestion.QUIZ,
                confidence=0.8,
                config={"type": "multiple_choice"}
            )
        
        return None
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code."""
        code_lower = code.lower()
        
        if "def " in code or "import " in code:
            return "python"
        elif "function " in code or "const " in code:
            return "javascript"
        elif "<html" in code_lower or "<div" in code_lower:
            return "html"
        elif "public class" in code or "private " in code:
            return "java"
        
        return "text"
    
    async def generate_html(
        self,
        markdown: str,
        theme: ThemeType,
        suggestions: List[SemanticSuggestion],
        approved_components: List[str]
    ) -> str:
        """Generate final HTML with interactive components."""
        # Filter to only approved suggestions
        approved_suggestions = [s for s in suggestions if s.block_id in approved_components]
        
        prompt = f"""Convert the following Markdown to responsive HTML with these requirements:

1. Theme: {theme.value}
2. Include responsive CSS
3. For blocks with component suggestions, inject interactive widgets:
{self._format_suggestions(approved_suggestions)}

Markdown content:
{markdown}

Generate complete, valid HTML with embedded CSS and JavaScript for interactivity.
Include Chart.js for charts, Prism.js for code highlighting.

HTML output:"""
        
        system_prompt = """You are an expert HTML/CSS/JavaScript developer. 
Generate clean, semantic, accessible HTML5 with embedded styles and scripts.
Use modern CSS (flexbox/grid) for responsive layouts."""
        
        try:
            html = await self._call_ernie(prompt, system_prompt)
            return self._post_process_html(html, theme)
        except Exception as e:
            logger.error(f"HTML generation failed: {e}")
            return self._generate_fallback_html(markdown, theme)
    
    def _format_suggestions(self, suggestions: List[SemanticSuggestion]) -> str:
        """Format suggestions for prompt."""
        if not suggestions:
            return "No interactive components requested."
        
        lines = []
        for s in suggestions:
            lines.append(f"- Block {s.block_id}: {s.suggestion.value} (config: {s.config})")
        return "\n".join(lines)
    
    def _post_process_html(self, html: str, theme: ThemeType) -> str:
        """Post-process generated HTML."""
        # Ensure proper DOCTYPE
        if not html.strip().lower().startswith("<!doctype"):
            html = "<!DOCTYPE html>\n" + html
        
        # Add theme class to body if not present
        if f'class="{theme.value}"' not in html:
            html = html.replace("<body>", f'<body class="theme-{theme.value}">')
        
        return html
    
    def _generate_fallback_html(self, markdown: str, theme: ThemeType) -> str:
        """Generate basic HTML when ERNIE fails."""
        import markdown as md
        
        html_content = md.markdown(markdown, extensions=['tables', 'fenced_code'])
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Converted Document</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: {"#1a1a2e" if theme == ThemeType.DARK else "#ffffff"};
            color: {"#eaeaea" if theme == ThemeType.DARK else "#333333"};
        }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 15px; overflow-x: auto; }}
    </style>
</head>
<body class="theme-{theme.value}">
    {html_content}
</body>
</html>"""


# Singleton instance
ernie_service = ERNIEService()
