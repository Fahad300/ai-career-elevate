"""
Comprehensive tests for PDF text extraction tools.
Tests multiple extraction methods and fallback scenarios.
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.tools.pdf_tools import (
    pdf_to_text,
    get_extraction_capabilities,
    _extract_with_pdfminer,
    _extract_with_pypdf,
    _extract_with_ocr,
    PDFExtractionResult
)


class TestPDFToolsBasic:
    """Test basic PDF tools functionality."""
    
    def test_get_extraction_capabilities(self):
        """Test getting extraction capabilities."""
        capabilities = get_extraction_capabilities()
        
        assert isinstance(capabilities, dict)
        assert "pdfminer" in capabilities
        assert "pypdf" in capabilities
        assert "ocr" in capabilities
        assert "pdf_to_image" in capabilities
        
        # All values should be booleans
        for key, value in capabilities.items():
            assert isinstance(value, bool)
    
    def test_pdf_to_text_invalid_input(self):
        """Test pdf_to_text with invalid inputs."""
        # Test non-string input
        result = pdf_to_text(123)
        assert result["text"] == ""
        assert result["method"] == "error"
        assert result["confidence"] == "low"
        assert "File path must be a string" in result["error"]
        
        # Test non-existent file
        result = pdf_to_text("non_existent_file.pdf")
        assert result["text"] == ""
        assert result["method"] == "error"
        assert result["confidence"] == "low"
        assert "File not found" in result["error"]
        
        # Test non-PDF file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Not a PDF file")
            temp_file = f.name
        
        try:
            result = pdf_to_text(temp_file)
            assert result["text"] == ""
            assert result["method"] == "error"
            assert result["confidence"] == "low"
            assert "File must be a PDF" in result["error"]
        finally:
            os.unlink(temp_file)


class TestPDFMinerExtraction:
    """Test pdfminer extraction functionality."""
    
    def test_extract_with_pdfminer_success(self):
        """Test successful pdfminer extraction."""
        with patch('app.tools.pdf_tools.pdfminer_extract') as mock_extract:
            mock_extract.return_value = "This is extracted text from PDF"
            
            result = _extract_with_pdfminer("test.pdf")
            
            assert result.text == "This is extracted text from PDF"
            assert result.method == "pdfminer"
            assert result.confidence == "medium"
            assert result.pages_processed == 1
            assert result.error is None
    
    def test_extract_with_pdfminer_high_confidence(self):
        """Test pdfminer extraction with high confidence."""
        long_text = "This is a very long extracted text from PDF. " * 10  # > 100 chars
        with patch('app.tools.pdf_tools.pdfminer_extract') as mock_extract:
            mock_extract.return_value = long_text
            
            result = _extract_with_pdfminer("test.pdf")
            
            assert result.text == long_text.strip()
            assert result.method == "pdfminer"
            assert result.confidence == "high"
            assert result.pages_processed == 1
    
    def test_extract_with_pdfminer_empty_text(self):
        """Test pdfminer extraction with empty text."""
        with patch('app.tools.pdf_tools.pdfminer_extract') as mock_extract:
            mock_extract.return_value = ""
            
            result = _extract_with_pdfminer("test.pdf")
            
            assert result.text == ""
            assert result.method == "pdfminer"
            assert result.confidence == "low"
            assert result.pages_processed == 0
            assert "No meaningful text extracted" in result.error
    
    def test_extract_with_pdfminer_exception(self):
        """Test pdfminer extraction with exception."""
        with patch('app.tools.pdf_tools.pdfminer_extract') as mock_extract:
            mock_extract.side_effect = Exception("PDF is corrupted")
            
            result = _extract_with_pdfminer("test.pdf")
            
            assert result.text == ""
            assert result.method == "pdfminer"
            assert result.confidence == "low"
            assert result.pages_processed == 0
            assert "pdfminer extraction failed" in result.error


class TestPyPDFExtraction:
    """Test pypdf extraction functionality."""
    
    def test_extract_with_pypdf_success(self):
        """Test successful pypdf extraction."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "This is extracted text from page"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        with patch('app.tools.pdf_tools.PdfReader') as mock_reader_class:
            mock_reader_class.return_value = mock_reader
            
            result = _extract_with_pypdf("test.pdf")
            
            assert result.text == "This is extracted text from page"
            assert result.method == "pypdf"
            assert result.confidence == "medium"
            assert result.pages_processed == 1
            assert result.error is None
    
    def test_extract_with_pypdf_multiple_pages(self):
        """Test pypdf extraction with multiple pages."""
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 text"
        
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 text"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]
        
        with patch('app.tools.pdf_tools.PdfReader') as mock_reader_class:
            mock_reader_class.return_value = mock_reader
            
            result = _extract_with_pypdf("test.pdf")
            
            assert "Page 1 text" in result.text
            assert "Page 2 text" in result.text
            assert result.method == "pypdf"
            assert result.confidence == "medium"
            assert result.pages_processed == 2
    
    def test_extract_with_pypdf_empty_text(self):
        """Test pypdf extraction with empty text."""
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        with patch('app.tools.pdf_tools.PdfReader') as mock_reader_class:
            mock_reader_class.return_value = mock_reader
            
            result = _extract_with_pypdf("test.pdf")
            
            assert result.text == ""
            assert result.method == "pypdf"
            assert result.confidence == "low"
            assert result.pages_processed == 0
            assert "No text extracted from any page" in result.error
    
    def test_extract_with_pypdf_exception(self):
        """Test pypdf extraction with exception."""
        with patch('app.tools.pdf_tools.PdfReader') as mock_reader_class:
            mock_reader_class.side_effect = Exception("Invalid PDF")
            
            result = _extract_with_pypdf("test.pdf")
            
            assert result.text == ""
            assert result.method == "pypdf"
            assert result.confidence == "low"
            assert result.pages_processed == 0
            assert "pypdf extraction failed" in result.error


class TestOCRExtraction:
    """Test OCR extraction functionality."""
    
    def test_extract_with_ocr_success(self):
        """Test successful OCR extraction."""
        mock_image = Mock()
        mock_images = [mock_image]
        
        with patch('app.tools.pdf_tools._pdf_to_images') as mock_pdf_to_images, \
             patch('app.tools.pdf_tools.pytesseract') as mock_tesseract:
            
            mock_pdf_to_images.return_value = mock_images
            mock_tesseract.image_to_string.return_value = "This is OCR extracted text"
            
            result = _extract_with_ocr("test.pdf")
            
            assert result.text == "This is OCR extracted text"
            assert result.method == "ocr"
            assert result.confidence == "medium"
            assert result.pages_processed == 1
            assert result.error is None
    
    def test_extract_with_ocr_high_confidence(self):
        """Test OCR extraction with high confidence."""
        long_text = "This is a very long OCR extracted text from scanned document. " * 10
        mock_image = Mock()
        mock_images = [mock_image]
        
        with patch('app.tools.pdf_tools._pdf_to_images') as mock_pdf_to_images, \
             patch('app.tools.pdf_tools.pytesseract') as mock_tesseract:
            
            mock_pdf_to_images.return_value = mock_images
            mock_tesseract.image_to_string.return_value = long_text
            
            result = _extract_with_ocr("test.pdf")
            
            assert result.text == long_text.strip()
            assert result.method == "ocr"
            assert result.confidence == "high"
            assert result.pages_processed == 1
    
    def test_extract_with_ocr_no_images(self):
        """Test OCR extraction when PDF to image conversion fails."""
        with patch('app.tools.pdf_tools._pdf_to_images') as mock_pdf_to_images:
            mock_pdf_to_images.return_value = []
            
            result = _extract_with_ocr("test.pdf")
            
            assert result.text == ""
            assert result.method == "ocr"
            assert result.confidence == "low"
            assert result.pages_processed == 0
            assert "Failed to convert PDF to images for OCR" in result.error
    
    def test_extract_with_ocr_exception(self):
        """Test OCR extraction with exception."""
        with patch('app.tools.pdf_tools._pdf_to_images') as mock_pdf_to_images:
            mock_pdf_to_images.side_effect = Exception("OCR failed")
            
            result = _extract_with_ocr("test.pdf")
            
            assert result.text == ""
            assert result.method == "ocr"
            assert result.confidence == "low"
            assert result.pages_processed == 0
            assert "OCR extraction failed" in result.error


class TestPDFToTextIntegration:
    """Test integrated pdf_to_text function."""
    
    def test_pdf_to_text_with_sample_file(self):
        """Test pdf_to_text with the sample PDF file."""
        sample_pdf = "samples/text_resume.pdf"
        
        if os.path.exists(sample_pdf):
            result = pdf_to_text(sample_pdf)
            
            # Should have some text extracted
            assert "text" in result
            assert "method" in result
            assert "confidence" in result
            
            # Method should be one of the expected values
            assert result["method"] in ["pdfminer", "pypdf", "ocr", "error", "fallback"]
            
            # Confidence should be one of the expected values
            assert result["confidence"] in ["high", "medium", "low"]
        else:
            pytest.skip("Sample PDF file not found")
    
    def test_pdf_to_text_fallback_behavior(self):
        """Test pdf_to_text fallback behavior when all methods fail."""
        with patch('app.tools.pdf_tools._extract_with_pdfminer') as mock_pdfminer, \
             patch('app.tools.pdf_tools._extract_with_pypdf') as mock_pypdf, \
             patch('app.tools.pdf_tools._extract_with_ocr') as mock_ocr:
            
            # Mock all methods to return empty results
            empty_result = PDFExtractionResult(
                text="",
                method="test",
                confidence="low",
                pages_processed=0,
                error="No text"
            )
            
            mock_pdfminer.return_value = empty_result
            mock_pypdf.return_value = empty_result
            mock_ocr.return_value = empty_result
            
            # Create a temporary PDF file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n")
                temp_file = f.name
            
            try:
                result = pdf_to_text(temp_file)
                
                # Should return the last method's result
                assert result["text"] == ""
                assert result["method"] == "test"  # Last method tried (mocked method name)
                assert result["confidence"] == "low"
                assert "No text" in result["error"]
            finally:
                os.unlink(temp_file)
    
    def test_pdf_to_text_method_priority(self):
        """Test that pdf_to_text tries methods in the correct priority order."""
        with patch('app.tools.pdf_tools._extract_with_pdfminer') as mock_pdfminer, \
             patch('app.tools.pdf_tools._extract_with_pypdf') as mock_pypdf, \
             patch('app.tools.pdf_tools._extract_with_ocr') as mock_ocr:
            
            # Mock pdfminer to succeed
            success_result = PDFExtractionResult(
                text="Success from pdfminer",
                method="pdfminer",
                confidence="high",
                pages_processed=1
            )
            mock_pdfminer.return_value = success_result
            
            # Create a temporary PDF file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n")
                temp_file = f.name
            
            try:
                result = pdf_to_text(temp_file)
                
                # Should use pdfminer result and not try other methods
                assert result["text"] == "Success from pdfminer"
                assert result["method"] == "pdfminer"
                assert result["confidence"] == "high"
                
                # Other methods should not have been called
                mock_pypdf.assert_not_called()
                mock_ocr.assert_not_called()
            finally:
                os.unlink(temp_file)


class TestPDFToolsErrorHandling:
    """Test error handling in PDF tools."""
    
    def test_pdf_to_text_with_corrupted_file(self):
        """Test pdf_to_text with corrupted PDF file."""
        # Create a file that looks like a PDF but is corrupted
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"This is not a valid PDF file content")
            temp_file = f.name
        
        try:
            result = pdf_to_text(temp_file)
            
            # Should handle the error gracefully
            assert "text" in result
            assert "method" in result
            assert "confidence" in result
            
            # Should either extract some text or report an error
            if result["method"] == "error":
                assert "error" in result
            else:
                assert result["method"] in ["pdfminer", "pypdf", "ocr", "fallback"]
        finally:
            os.unlink(temp_file)
    
    def test_pdf_to_text_with_empty_file(self):
        """Test pdf_to_text with empty PDF file."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"")
            temp_file = f.name
        
        try:
            result = pdf_to_text(temp_file)
            
            # Should handle empty file gracefully
            assert "text" in result
            assert "method" in result
            assert "confidence" in result
        finally:
            os.unlink(temp_file)


class TestPDFToolsMocking:
    """Test PDF tools with various mocking scenarios."""
    
    def test_pdf_to_text_all_methods_unavailable(self):
        """Test pdf_to_text when all extraction methods are unavailable."""
        with patch('app.tools.pdf_tools.PDFMINER_AVAILABLE', False), \
             patch('app.tools.pdf_tools.PYPDF_AVAILABLE', False), \
             patch('app.tools.pdf_tools.OCR_AVAILABLE', False):
            
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n")
                temp_file = f.name
            
            try:
                result = pdf_to_text(temp_file)
                
                # Should return fallback result
                assert result["text"] == ""
                assert result["method"] == "fallback"
                assert result["confidence"] == "low"
                assert "All extraction methods failed" in result["error"]
            finally:
                os.unlink(temp_file)
    
    def test_pdf_to_text_partial_method_availability(self):
        """Test pdf_to_text with only some methods available."""
        with patch('app.tools.pdf_tools.PDFMINER_AVAILABLE', False), \
             patch('app.tools.pdf_tools.PYPDF_AVAILABLE', True), \
             patch('app.tools.pdf_tools.OCR_AVAILABLE', False):
            
            with patch('app.tools.pdf_tools._extract_with_pypdf') as mock_pypdf:
                mock_pypdf.return_value = PDFExtractionResult(
                    text="Text from pypdf",
                    method="pypdf",
                    confidence="medium",
                    pages_processed=1
                )
                
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n")
                    temp_file = f.name
                
                try:
                    result = pdf_to_text(temp_file)
                    
                    # Should use pypdf result
                    assert result["text"] == "Text from pypdf"
                    assert result["method"] == "pypdf"
                    assert result["confidence"] == "medium"
                finally:
                    os.unlink(temp_file)
