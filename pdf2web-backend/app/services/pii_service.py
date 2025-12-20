"""PII Detection and Sanitization Service using Presidio/spaCy (Secure Mode)."""
import uuid
from typing import List, Tuple, Optional
from loguru import logger

from app.models.schemas import ContentBlock, PIIRedaction
from app.config import settings


class PIIService:
    """Service for detecting and redacting PII locally (Secure Mode)."""
    
    def __init__(self):
        self._analyzer = None
        self._anonymizer = None
        self._initialized = False
        self._spacy_nlp = None
    
    def _initialize(self):
        """Lazy initialize Presidio and spaCy components."""
        if self._initialized:
            return
        
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            
            self._analyzer = AnalyzerEngine()
            self._anonymizer = AnonymizerEngine()
            self._initialized = True
            logger.info("Presidio PII service initialized")
            
        except ImportError:
            logger.warning("Presidio not available, trying spaCy fallback")
            try:
                import spacy
                self._spacy_nlp = spacy.load("en_core_web_lg")
                logger.info("spaCy NLP loaded as PII fallback")
            except Exception:
                logger.warning("Neither Presidio nor spaCy available")
            self._initialized = True
    
    async def scan_and_redact(
        self, 
        blocks: List[ContentBlock],
        threshold: float = None,
        config: dict = None
    ) -> Tuple[List[ContentBlock], List[PIIRedaction]]:
        """
        Scan content blocks for PII and redact them (Secure Mode).
        
        Args:
            blocks: List of content blocks to scan
            threshold: Confidence threshold for PII detection
            config: SecureModeConfig options (redact_emails, redact_phones, etc.)
            
        Returns:
            Tuple of (redacted_blocks, redaction_records)
        """
        self._initialize()
        
        # Default config
        if config is None:
            config = {
                "redact_emails": True,
                "redact_phones": True,
                "redact_names": True,
                "redact_ssn": True,
                "redact_credit_cards": True
            }
        
        # Build entity list based on config
        entities = []
        if config.get("redact_phones", True):
            entities.append("PHONE_NUMBER")
        if config.get("redact_emails", True):
            entities.append("EMAIL_ADDRESS")
        if config.get("redact_names", True):
            entities.append("PERSON")
        if config.get("redact_ssn", True):
            entities.append("US_SSN")
        if config.get("redact_credit_cards", True):
            entities.append("CREDIT_CARD")
        entities.extend(["US_PASSPORT", "US_DRIVER_LICENSE", "IP_ADDRESS"])
        
        if not self._analyzer and not self._spacy_nlp:
            logger.warning("PII analyzer not available, returning original content")
            return blocks, []
        
        threshold = threshold or settings.pii_detection_threshold
        redacted_blocks = []
        all_redactions = []
        
        for block in blocks:
            if self._analyzer:
                redacted_content, redactions = await self._process_block(block, threshold, entities)
            else:
                redacted_content, redactions = await self._process_block_spacy(block, config)
            
            # Create new block with redacted content
            redacted_block = block.model_copy()
            redacted_block.content = redacted_content
            redacted_blocks.append(redacted_block)
            
            all_redactions.extend(redactions)
        
        logger.info(f"Secure Mode: Redacted {len(all_redactions)} PII instances")
        return redacted_blocks, all_redactions
    
    async def _process_block_spacy(
        self, 
        block: ContentBlock, 
        config: dict
    ) -> Tuple[str, List[PIIRedaction]]:
        """Process block using spaCy NER as fallback."""
        import re
        content = block.content
        redactions = []
        
        if self._spacy_nlp:
            doc = self._spacy_nlp(content)
            
            # Sort entities by position (reverse for replacement)
            entities = sorted(doc.ents, key=lambda e: e.start_char, reverse=True)
            
            for ent in entities:
                pii_type = None
                if ent.label_ == "PERSON" and config.get("redact_names", True):
                    pii_type = "PERSON"
                elif ent.label_ in ["ORG", "GPE"] and config.get("redact_names", True):
                    continue  # Skip organizations/locations
                
                if pii_type:
                    redacted_text = self._get_redaction_placeholder(pii_type)
                    redaction = PIIRedaction(
                        id=str(uuid.uuid4()),
                        original=ent.text,
                        redacted=redacted_text,
                        pii_type=pii_type,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.8,
                        block_id=block.id
                    )
                    redactions.append(redaction)
                    content = content[:ent.start_char] + redacted_text + content[ent.end_char:]
        
        # Regex patterns for emails and phones
        if config.get("redact_emails", True):
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            for match in re.finditer(email_pattern, content):
                redactions.append(PIIRedaction(
                    id=str(uuid.uuid4()),
                    original=match.group(),
                    redacted="[EMAIL_REDACTED]",
                    pii_type="EMAIL_ADDRESS",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.95,
                    block_id=block.id
                ))
            content = re.sub(email_pattern, "[EMAIL_REDACTED]", content)
        
        if config.get("redact_phones", True):
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            for match in re.finditer(phone_pattern, content):
                redactions.append(PIIRedaction(
                    id=str(uuid.uuid4()),
                    original=match.group(),
                    redacted="[PHONE_REDACTED]",
                    pii_type="PHONE_NUMBER",
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9,
                    block_id=block.id
                ))
            content = re.sub(phone_pattern, "[PHONE_REDACTED]", content)
        
        return content, redactions
    
    async def _process_block(
        self, 
        block: ContentBlock, 
        threshold: float,
        entities: List[str] = None
    ) -> Tuple[str, List[PIIRedaction]]:
        """Process a single block for PII."""
        content = block.content
        redactions = []
        
        # Analyze for PII
        if entities is None:
            entities = [
                "PHONE_NUMBER", "EMAIL_ADDRESS", "PERSON", "US_SSN",
                "CREDIT_CARD", "US_PASSPORT", "US_DRIVER_LICENSE", "IP_ADDRESS"
            ]
        
        results = self._analyzer.analyze(
            text=content,
            language="en",
            entities=entities
        )
        
        # Filter by threshold and sort by position (reverse for replacement)
        filtered_results = [r for r in results if r.score >= threshold]
        filtered_results.sort(key=lambda x: x.start, reverse=True)
        
        # Redact each PII instance
        redacted_content = content
        for result in filtered_results:
            original_text = content[result.start:result.end]
            redacted_text = self._get_redaction_placeholder(result.entity_type)
            
            # Create redaction record
            redaction = PIIRedaction(
                id=str(uuid.uuid4()),
                original=original_text,
                redacted=redacted_text,
                pii_type=result.entity_type,
                start=result.start,
                end=result.end,
                confidence=result.score,
                block_id=block.id
            )
            redactions.append(redaction)
            
            # Apply redaction
            redacted_content = (
                redacted_content[:result.start] + 
                redacted_text + 
                redacted_content[result.end:]
            )
        
        return redacted_content, redactions
    
    def _get_redaction_placeholder(self, entity_type: str) -> str:
        """Get appropriate placeholder for PII type."""
        placeholders = {
            "PHONE_NUMBER": "[PHONE_REDACTED]",
            "EMAIL_ADDRESS": "[EMAIL_REDACTED]",
            "PERSON": "[NAME_REDACTED]",
            "US_SSN": "[SSN_REDACTED]",
            "CREDIT_CARD": "[CARD_REDACTED]",
            "US_PASSPORT": "[PASSPORT_REDACTED]",
            "US_DRIVER_LICENSE": "[LICENSE_REDACTED]",
            "IP_ADDRESS": "[IP_REDACTED]",
            "DATE_TIME": "[DATE_REDACTED]",
            "LOCATION": "[LOCATION_REDACTED]"
        }
        return placeholders.get(entity_type, "[REDACTED]")
    
    async def undo_redaction(
        self, 
        content: str, 
        redaction: PIIRedaction
    ) -> str:
        """Undo a specific redaction (restore original text)."""
        return content.replace(redaction.redacted, redaction.original, 1)
    
    async def get_pii_summary(self, redactions: List[PIIRedaction]) -> dict:
        """Get summary of detected PII types."""
        summary = {}
        for redaction in redactions:
            pii_type = redaction.pii_type
            if pii_type not in summary:
                summary[pii_type] = {"count": 0, "avg_confidence": 0}
            summary[pii_type]["count"] += 1
            summary[pii_type]["avg_confidence"] += redaction.confidence
        
        # Calculate averages
        for pii_type in summary:
            count = summary[pii_type]["count"]
            summary[pii_type]["avg_confidence"] /= count
        
        return summary


# Singleton instance
pii_service = PIIService()
