"""OCR Service using PaddleOCR for local text extraction."""
import os
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from loguru import logger

# Suppress PaddleOCR model connectivity check warning
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

from app.models.schemas import ContentBlock, ContentType
from app.config import settings


class OCRService:
    """Service for OCR extraction using PaddleOCR."""
    
    def __init__(self):
        self._ocr = None
    
    @property
    def ocr(self):
        """Lazy load PaddleOCR to avoid startup delay."""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                import logging
                # Suppress PaddleOCR logging
                logging.getLogger("ppocr").setLevel(logging.WARNING)
                logger.info("Initializing PaddleOCR...")
                # Use minimal params for compatibility with newer PaddleOCR/PaddleX
                self._ocr = PaddleOCR(
                    lang=settings.ocr_language,
                    device="cpu"
                )
                logger.info("PaddleOCR initialized successfully")
            except ImportError as e:
                logger.warning(f"PaddleOCR not available: {e}")
                self._ocr = None
            except Exception as e:
                import traceback
                logger.warning(f"PaddleOCR initialization failed: {e}")
                logger.warning(f"PaddleOCR init traceback: {traceback.format_exc()}")
                self._ocr = None
        return self._ocr
    
    async def extract_from_pdf(
        self, 
        pdf_path: Path,
        save_page_images: bool = True
    ) -> Tuple[List[ContentBlock], List[str], Dict[int, str]]:
        """
        Extract text and images from PDF using PaddleOCR.
        
        Args:
            pdf_path: Path to the PDF file
            save_page_images: Whether to save page images for vision analysis
        
        Returns:
            Tuple of (content_blocks, image_paths, page_images)
            - content_blocks: List of extracted content blocks
            - image_paths: List of extracted image paths
            - page_images: Dict mapping page numbers to page image paths (for vision analysis)
        """
        import fitz  # PyMuPDF
        
        blocks: List[ContentBlock] = []
        image_paths: List[str] = []
        page_images: Dict[int, str] = {}
        doc = None
        
        try:
            logger.info(f"Opening PDF: {pdf_path}")
            doc = fitz.open(str(pdf_path))
            total_pages = min(len(doc), settings.max_pages)
            logger.info(f"PDF opened: {total_pages} pages")
            
            for page_num in range(total_pages):
                logger.debug(f"Processing page {page_num + 1}/{total_pages}")
                page = doc[page_num]
                
                # Save page image for vision analysis
                if save_page_images:
                    page_img_path = await self._save_page_image(
                        page, pdf_path.stem, page_num
                    )
                    if page_img_path:
                        page_images[page_num] = page_img_path
                
                # Extract images
                images = self._extract_images(page, pdf_path.stem, page_num)
                image_paths.extend(images)
                
                # Extract text blocks
                page_blocks = await self._extract_page_content(page, page_num)
                blocks.extend(page_blocks)
            
            logger.info(f"Extracted {len(blocks)} blocks, {len(image_paths)} images, {len(page_images)} page images")
            
        except Exception as e:
            import traceback
            logger.error(f"PDF extraction failed: {e}")
            logger.error(f"Extraction traceback: {traceback.format_exc()}")
            raise
        finally:
            if doc:
                doc.close()
        
        return blocks, image_paths, page_images
    
    async def _save_page_image(self, page, doc_name: str, page_num: int) -> Optional[str]:
        """Save a page as an image for vision analysis."""
        try:
            # Render page at configured DPI
            pix = page.get_pixmap(dpi=settings.image_dpi)
            
            # Save to temp directory
            image_filename = f"{doc_name}_page_{page_num}.png"
            image_path = settings.upload_dir / "pages" / image_filename
            image_path.parent.mkdir(parents=True, exist_ok=True)
            
            pix.save(str(image_path))
            return str(image_path)
            
        except Exception as e:
            logger.warning(f"Failed to save page {page_num} image: {e}")
            return None
    
    def _extract_images(self, page, doc_name: str, page_num: int) -> List[str]:
        """Extract images from a PDF page."""
        image_paths = []
        image_list = page.get_images()
        
        for img_idx, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Save image locally
                image_filename = f"{doc_name}_p{page_num}_img{img_idx}.{image_ext}"
                image_path = settings.upload_dir / "images" / image_filename
                image_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                
                image_paths.append(str(image_path))
                
            except Exception as e:
                logger.warning(f"Failed to extract image {img_idx} on page {page_num}: {e}")
        
        return image_paths
    
    async def _extract_page_content(self, page, page_num: int) -> List[ContentBlock]:
        """Extract content blocks from a single page."""
        blocks = []
        
        # Get text blocks with positions
        text_dict = page.get_text("dict")
        
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                content_block = self._process_text_block(block, page_num)
                if content_block:
                    blocks.append(content_block)
        
        # If PaddleOCR is available, enhance with OCR
        if self.ocr:
            blocks = await self._enhance_with_ocr(page, blocks, page_num)
        
        return blocks
    
    def _process_text_block(self, block: dict, page_num: int) -> Optional[ContentBlock]:
        """Process a text block from PyMuPDF."""
        lines = block.get("lines", [])
        if not lines:
            return None
        
        # Combine text from all spans
        text_parts = []
        for line in lines:
            for span in line.get("spans", []):
                text_parts.append(span.get("text", ""))
        
        content = " ".join(text_parts).strip()
        if not content:
            return None
        
        # Determine content type based on formatting
        content_type = self._classify_content_type(block, content)
        
        return ContentBlock(
            id=str(uuid.uuid4()),
            type=content_type,
            content=content,
            page=page_num,
            confidence=0.95,  # PyMuPDF extraction is reliable
            bbox=block.get("bbox"),
            metadata={
                "font_size": self._get_avg_font_size(lines),
                "is_bold": self._check_bold(lines)
            }
        )
    
    def _classify_content_type(self, block: dict, content: str) -> ContentType:
        """Classify content type based on formatting and content."""
        lines = block.get("lines", [])
        avg_font_size = self._get_avg_font_size(lines)
        is_bold = self._check_bold(lines)
        
        # Heading detection
        if avg_font_size > 14 or (is_bold and len(content) < 100):
            return ContentType.HEADING
        
        # List detection
        if content.strip().startswith(("-", "•", "*", "1.", "2.", "a)", "b)")):
            return ContentType.LIST
        
        # Code detection
        if "```" in content or content.count("    ") > 2:
            return ContentType.CODE
        
        # Table detection (basic)
        if "|" in content and content.count("|") > 2:
            return ContentType.TABLE
        
        return ContentType.PARAGRAPH
    
    def _get_avg_font_size(self, lines: list) -> float:
        """Get average font size from lines."""
        sizes = []
        for line in lines:
            for span in line.get("spans", []):
                sizes.append(span.get("size", 12))
        return sum(sizes) / len(sizes) if sizes else 12
    
    def _check_bold(self, lines: list) -> bool:
        """Check if text is bold."""
        for line in lines:
            for span in line.get("spans", []):
                flags = span.get("flags", 0)
                if flags & 2 ** 4:  # Bold flag
                    return True
        return False
    
    async def _enhance_with_ocr(self, page, blocks: List[ContentBlock], page_num: int) -> List[ContentBlock]:
        """Enhance extraction with PaddleOCR for scanned content."""
        # Skip OCR enhancement if we already have good text extraction from PyMuPDF
        if len(blocks) > 0:
            logger.debug(f"Skipping OCR enhancement - PyMuPDF already extracted {len(blocks)} blocks")
            return blocks
        
        try:
            # Convert page to image for OCR
            pix = page.get_pixmap(dpi=settings.image_dpi)
            img_path = settings.upload_dir / "temp" / f"ocr_temp_{page_num}.png"
            img_path.parent.mkdir(parents=True, exist_ok=True)
            pix.save(str(img_path))
            
            # Run OCR with timeout protection
            result = None
            try:
                logger.debug(f"Running OCR on page {page_num}...")
                import asyncio
                import concurrent.futures
                
                # Run OCR in thread pool with timeout
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    try:
                        # 30 second timeout for OCR
                        if hasattr(self.ocr, 'predict'):
                            future = loop.run_in_executor(pool, self.ocr.predict, str(img_path))
                        else:
                            future = loop.run_in_executor(pool, lambda: self.ocr.ocr(str(img_path)))
                        result = await asyncio.wait_for(future, timeout=30.0)
                        logger.debug(f"OCR result type: {type(result)}")
                    except asyncio.TimeoutError:
                        logger.warning(f"OCR timed out for page {page_num}, skipping enhancement")
                        img_path.unlink(missing_ok=True)
                        return blocks
            except Exception as ocr_err:
                logger.warning(f"OCR failed for page {page_num}: {ocr_err}")
                img_path.unlink(missing_ok=True)
                return blocks
            
            if result and len(result) > 0:
                # Handle different result formats
                ocr_result = result[0] if isinstance(result[0], list) else result
                for item in ocr_result:
                    try:
                        if isinstance(item, dict):
                            # New format: dict with 'rec_texts', 'rec_scores', 'dt_polys'
                            texts = item.get('rec_texts', [])
                            scores = item.get('rec_scores', [])
                            polys = item.get('dt_polys', [])
                            for i, text in enumerate(texts):
                                confidence = scores[i] if i < len(scores) else 0.5
                                # Convert polygon to bbox [x, y, width, height]
                                bbox = None
                                if i < len(polys):
                                    poly = polys[i].tolist() if hasattr(polys[i], 'tolist') else polys[i]
                                    bbox = self._polygon_to_bbox(poly)
                                if confidence > 0.5 and not self._text_exists(text, blocks):
                                    blocks.append(ContentBlock(
                                        id=str(uuid.uuid4()),
                                        type=ContentType.PARAGRAPH,
                                        content=text,
                                        page=page_num,
                                        confidence=confidence,
                                        bbox=bbox,
                                        metadata={"source": "paddleocr"}
                                    ))
                        elif isinstance(item, (list, tuple)) and len(item) >= 2:
                            # Old format: [bbox, (text, confidence)]
                            raw_bbox, text_conf = item[0], item[1]
                            text, confidence = text_conf if isinstance(text_conf, tuple) else (text_conf, 0.5)
                            # Convert polygon to bbox [x, y, width, height]
                            bbox = self._polygon_to_bbox(raw_bbox)
                            if confidence > 0.5 and not self._text_exists(text, blocks):
                                blocks.append(ContentBlock(
                                    id=str(uuid.uuid4()),
                                    type=ContentType.PARAGRAPH,
                                    content=text,
                                    page=page_num,
                                    confidence=confidence,
                                    bbox=bbox,
                                    metadata={"source": "paddleocr"}
                                ))
                    except Exception as item_err:
                        logger.debug(f"Skipping OCR item: {item_err}")
            
            # Cleanup temp file
            img_path.unlink(missing_ok=True)
            
        except Exception as e:
            logger.warning(f"OCR enhancement failed for page {page_num}: {e}")
        
        return blocks
    
    def _text_exists(self, text: str, blocks: List[ContentBlock]) -> bool:
        """Check if text already exists in blocks."""
        text_lower = text.lower().strip()
        for block in blocks:
            if text_lower in block.content.lower():
                return True
        return False

    def _polygon_to_bbox(self, polygon) -> Optional[List[float]]:
        """Convert polygon coordinates to bbox [x, y, width, height]."""
        try:
            if not polygon:
                return None
            # Polygon is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] or similar
            if isinstance(polygon[0], (list, tuple)):
                xs = [float(p[0]) for p in polygon]
                ys = [float(p[1]) for p in polygon]
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)
                return [x_min, y_min, x_max - x_min, y_max - y_min]
            # Already flat [x, y, w, h]
            elif len(polygon) == 4:
                return [float(v) for v in polygon]
            return None
        except Exception:
            return None


# Singleton instance
ocr_service = OCRService()
