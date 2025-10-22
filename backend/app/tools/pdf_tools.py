"""
PDF text extraction tools for AI Career Elevate.
Provides multiple extraction methods with fallback support.
"""
import os
import io
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel

# PDF processing imports
try:
    from pdfminer.high_level import extract_text as pdfminer_extract
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfpage import PDFPage
    from io import StringIO
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False
    logging.warning("pdfminer.six not available")

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    logging.warning("pypdf not available")

# OCR imports
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("OCR libraries (pytesseract, Pillow) not available")

# PDF to image conversion
try:
    import fitz  # PyMuPDF
    PDF_TO_IMAGE_AVAILABLE = True
except ImportError:
    try:
        from pdf2image import convert_from_path
        PDF_TO_IMAGE_AVAILABLE = True
        PDF_CONVERTER = "pdf2image"
    except ImportError:
        PDF_TO_IMAGE_AVAILABLE = False
        logging.warning("PDF to image conversion libraries not available")


class PDFExtractionResult(BaseModel):
    """Result model for PDF text extraction."""
    text: str
    method: str  # "pdfminer", "pypdf", "ocr", "fallback"
    confidence: str  # "high", "medium", "low"
    pages_processed: int = 0
    error: Optional[str] = None


def _extract_with_pdfminer(file_path: str) -> PDFExtractionResult:
    """Extract text using pdfminer.six."""
    try:
        text = pdfminer_extract(file_path)
        
        # Check if text extraction was successful
        if text and len(text.strip()) > 10:  # Minimum meaningful text length
            return PDFExtractionResult(
                text=text.strip(),
                method="pdfminer",
                confidence="high" if len(text) > 100 else "medium",
                pages_processed=1
            )
        else:
            return PDFExtractionResult(
                text="",
                method="pdfminer",
                confidence="low",
                pages_processed=0,
                error="No meaningful text extracted"
            )
    except Exception as e:
        return PDFExtractionResult(
            text="",
            method="pdfminer",
            confidence="low",
            pages_processed=0,
            error=f"pdfminer extraction failed: {str(e)}"
        )


def _extract_with_pypdf(file_path: str) -> PDFExtractionResult:
    """Extract text using pypdf."""
    try:
        reader = PdfReader(file_path)
        text_parts = []
        pages_processed = 0
        
        for page in reader.pages:
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_parts.append(page_text.strip())
                    pages_processed += 1
            except Exception as e:
                logging.warning(f"Failed to extract text from page {pages_processed + 1}: {e}")
                continue
        
        if text_parts:
            full_text = "\n\n".join(text_parts)
            return PDFExtractionResult(
                text=full_text,
                method="pypdf",
                confidence="high" if len(full_text) > 100 else "medium",
                pages_processed=pages_processed
            )
        else:
            return PDFExtractionResult(
                text="",
                method="pypdf",
                confidence="low",
                pages_processed=0,
                error="No text extracted from any page"
            )
    except Exception as e:
        return PDFExtractionResult(
            text="",
            method="pypdf",
            confidence="low",
            pages_processed=0,
            error=f"pypdf extraction failed: {str(e)}"
        )


def _pdf_to_images(file_path: str) -> list:
    """Convert PDF pages to images for OCR processing."""
    images = []
    
    try:
        if PDF_TO_IMAGE_AVAILABLE and 'fitz' in globals():
            # Using PyMuPDF
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
            doc.close()
            
        elif PDF_TO_IMAGE_AVAILABLE and PDF_CONVERTER == "pdf2image":
            # Using pdf2image
            images = convert_from_path(file_path, dpi=200)
            
    except Exception as e:
        logging.error(f"Failed to convert PDF to images: {e}")
    
    return images


def _extract_with_ocr(file_path: str) -> PDFExtractionResult:
    """Extract text using OCR on PDF pages."""
    try:
        # Convert PDF to images
        images = _pdf_to_images(file_path)
        
        if not images:
            return PDFExtractionResult(
                text="",
                method="ocr",
                confidence="low",
                pages_processed=0,
                error="Failed to convert PDF to images for OCR"
            )
        
        # Extract text from each image using OCR
        text_parts = []
        pages_processed = 0
        
        for img in images:
            try:
                # Use pytesseract for OCR
                page_text = pytesseract.image_to_string(img, config='--psm 6')
                if page_text and page_text.strip():
                    text_parts.append(page_text.strip())
                    pages_processed += 1
            except Exception as e:
                logging.warning(f"OCR failed on page {pages_processed + 1}: {e}")
                continue
        
        if text_parts:
            full_text = "\n\n".join(text_parts)
            # Estimate confidence based on text length and structure
            confidence = "high" if len(full_text) > 200 and any(char.isalpha() for char in full_text) else "medium"
            return PDFExtractionResult(
                text=full_text,
                method="ocr",
                confidence=confidence,
                pages_processed=pages_processed
            )
        else:
            return PDFExtractionResult(
                text="",
                method="ocr",
                confidence="low",
                pages_processed=0,
                error="No text extracted via OCR"
            )
    except Exception as e:
        return PDFExtractionResult(
            text="",
            method="ocr",
            confidence="low",
            pages_processed=0,
            error=f"OCR extraction failed: {str(e)}"
        )


def pdf_to_text(file_path: str) -> Dict[str, Any]:
    """
    Extract text from PDF using multiple methods with fallback.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Dict containing text, method, confidence, and metadata
    """
    # Validate input
    if not isinstance(file_path, str):
        return {
            "text": "",
            "method": "error",
            "confidence": "low",
            "error": "File path must be a string"
        }
    
    # Check if file exists
    if not os.path.exists(file_path):
        return {
            "text": "",
            "method": "error", 
            "confidence": "low",
            "error": "File not found"
        }
    
    # Check file extension
    if not file_path.lower().endswith('.pdf'):
        return {
            "text": "",
            "method": "error",
            "confidence": "low", 
            "error": "File must be a PDF"
        }
    
    # Try extraction methods in order of preference
    methods_to_try = []
    
    # Add available methods
    if PDFMINER_AVAILABLE:
        methods_to_try.append(_extract_with_pdfminer)
    if PYPDF_AVAILABLE:
        methods_to_try.append(_extract_with_pypdf)
    if OCR_AVAILABLE and PDF_TO_IMAGE_AVAILABLE:
        methods_to_try.append(_extract_with_ocr)
    
    # Try each method until we get meaningful text
    for method_func in methods_to_try:
        try:
            result = method_func(file_path)
            
            # If we got meaningful text, return it
            if result.text and len(result.text.strip()) > 10:
                return {
                    "text": result.text,
                    "method": result.method,
                    "confidence": result.confidence,
                    "pages_processed": result.pages_processed,
                    "error": result.error
                }
            
            # If this was our last method, return the result even if empty
            if method_func == methods_to_try[-1]:
                return {
                    "text": result.text,
                    "method": result.method,
                    "confidence": result.confidence,
                    "pages_processed": result.pages_processed,
                    "error": result.error
                }
                
        except Exception as e:
            logging.error(f"Method {method_func.__name__} failed: {e}")
            continue
    
    # If all methods failed
    return {
        "text": "",
        "method": "fallback",
        "confidence": "low",
        "error": "All extraction methods failed"
    }


def get_extraction_capabilities() -> Dict[str, bool]:
    """Get information about available extraction capabilities."""
    return {
        "pdfminer": PDFMINER_AVAILABLE,
        "pypdf": PYPDF_AVAILABLE,
        "ocr": OCR_AVAILABLE,
        "pdf_to_image": PDF_TO_IMAGE_AVAILABLE
    }
