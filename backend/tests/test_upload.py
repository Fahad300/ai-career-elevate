import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, AsyncMock
from io import BytesIO

from fastapi.testclient import TestClient
from fastapi import UploadFile, HTTPException

from app.main import app
from app.api.routes.upload import (
    validate_file_extension,
    validate_file_size,
    create_session_directory,
    upload_resume,
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS
)


class TestUploadValidation:
    """Test file validation functions."""
    
    def test_validate_file_extension_valid_pdf(self):
        """Test valid PDF file extension."""
        assert validate_file_extension("resume.pdf") is True
        assert validate_file_extension("RESUME.PDF") is True
        assert validate_file_extension("path/to/resume.pdf") is True
    
    def test_validate_file_extension_valid_docx(self):
        """Test valid DOCX file extension."""
        assert validate_file_extension("resume.docx") is True
        assert validate_file_extension("RESUME.DOCX") is True
        assert validate_file_extension("path/to/resume.docx") is True
    
    def test_validate_file_extension_invalid_extensions(self):
        """Test invalid file extensions."""
        invalid_extensions = [".txt", ".jpg", ".png", ".doc", ".rtf", ".odt"]
        for ext in invalid_extensions:
            assert validate_file_extension(f"file{ext}") is False
    
    def test_validate_file_size_valid(self):
        """Test valid file sizes."""
        assert validate_file_size(1024) is True  # 1KB
        assert validate_file_size(MAX_FILE_SIZE) is True  # Exactly 10MB
        assert validate_file_size(MAX_FILE_SIZE - 1) is True  # Just under 10MB
    
    def test_validate_file_size_invalid(self):
        """Test invalid file sizes."""
        assert validate_file_size(MAX_FILE_SIZE + 1) is False  # Just over 10MB
        assert validate_file_size(MAX_FILE_SIZE * 2) is False  # 20MB


class TestSessionDirectory:
    """Test session directory creation."""
    
    @patch('app.api.routes.upload.settings')
    def test_create_session_directory(self, mock_settings):
        """Test session directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings.storage_path = temp_dir
            session_id = "test-session-123"
            
            session_dir = create_session_directory(session_id)
            
            assert session_dir.exists()
            assert session_dir.is_dir()
            assert session_dir.name == session_id
            assert session_dir.parent == Path(temp_dir)


class TestUploadEndpoint:
    """Test the upload endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_file_content(self):
        """Create mock file content."""
        return b"Mock PDF content for testing"
    
    @pytest.mark.asyncio
    async def test_upload_resume_success_pdf(self, mock_file_content):
        """Test successful PDF upload."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('app.api.routes.upload.settings') as mock_settings:
                mock_settings.storage_path = temp_dir
                
                # Create mock UploadFile
                mock_file = Mock(spec=UploadFile)
                mock_file.filename = "test_resume.pdf"
                mock_file.size = len(mock_file_content)
                mock_file.read = AsyncMock(return_value=mock_file_content)
                
                # Call the endpoint
                response = await upload_resume(file=mock_file)

                # Verify response
                assert "session_id" in response
                assert "filename" in response
                assert response["filename"] == "test_resume.pdf"
                assert response["file_size"] == len(mock_file_content)
                assert response["message"] == "File uploaded successfully"
                
                # Verify file was saved
                session_id = response["session_id"]
                expected_path = Path(temp_dir) / session_id / "test_resume.pdf"
                assert expected_path.exists()
    
    @pytest.mark.asyncio
    async def test_upload_resume_success_docx(self, mock_file_content):
        """Test successful DOCX upload."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('app.api.routes.upload.settings') as mock_settings:
                mock_settings.storage_path = temp_dir
                
                # Create mock UploadFile
                mock_file = Mock(spec=UploadFile)
                mock_file.filename = "test_resume.docx"
                mock_file.size = len(mock_file_content)
                mock_file.read = AsyncMock(return_value=mock_file_content)
                
                # Call the endpoint
                response = await upload_resume(file=mock_file)

                # Verify response
                assert response["filename"] == "test_resume.docx"
                assert response["file_size"] == len(mock_file_content)
    
    @pytest.mark.asyncio
    async def test_upload_resume_invalid_extension(self, mock_file_content):
        """Test upload with invalid file extension."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test_resume.txt"
        mock_file.size = len(mock_file_content)
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_resume(file=mock_file)
        
        assert exc_info.value.status_code == 400
        assert "Invalid file type" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_upload_resume_file_too_large(self, mock_file_content):
        """Test upload with file too large."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test_resume.pdf"
        mock_file.size = MAX_FILE_SIZE + 1
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_resume(file=mock_file)
        
        assert exc_info.value.status_code == 413
        assert "File too large" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_upload_resume_no_filename(self, mock_file_content):
        """Test upload with no filename."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = None
        mock_file.size = len(mock_file_content)
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_resume(file=mock_file)
        
        assert exc_info.value.status_code == 400
        assert "Invalid file type" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_upload_resume_file_read_error(self):
        """Test upload with file read error."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test_resume.pdf"
        mock_file.size = 1024
        mock_file.read = AsyncMock(side_effect=Exception("File read error"))
        
        with pytest.raises(HTTPException) as exc_info:
            await upload_resume(file=mock_file)
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail


class TestUploadEndpointIntegration:
    """Test upload endpoint with TestClient."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('app.api.routes.upload.settings') as mock_settings:
                mock_settings.storage_path = temp_dir
                yield temp_dir
    
    def test_upload_endpoint_success(self, client, temp_storage):
        """Test successful upload via HTTP endpoint."""
        # Create test file
        file_content = b"Mock PDF content"
        files = {"file": ("test_resume.pdf", BytesIO(file_content), "application/pdf")}
        
        response = client.post("/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["filename"] == "test_resume.pdf"
        assert data["file_size"] == len(file_content)
    
    def test_upload_endpoint_invalid_file_type(self, client):
        """Test upload endpoint with invalid file type."""
        file_content = b"Mock text content"
        files = {"file": ("test_resume.txt", BytesIO(file_content), "text/plain")}
        response = client.post("/upload", files=files)
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    def test_upload_endpoint_no_file(self, client):
        """Test upload endpoint without file."""
        response = client.post("/upload")
        
        assert response.status_code == 422  # Validation error
    
    def test_upload_endpoint_multiple_files(self, client):
        """Test upload endpoint with multiple files (should only accept one)."""
        file_content = b"Mock PDF content"
        files = [
            ("file", ("test1.pdf", BytesIO(file_content), "application/pdf")),
            ("file", ("test2.pdf", BytesIO(file_content), "application/pdf"))
        ]
        
        response = client.post("/upload", files=files)
        
        # Should still work, but only process the first file
        assert response.status_code == 200


class TestUploadConstants:
    """Test upload constants and configuration."""
    
    def test_max_file_size_constant(self):
        """Test MAX_FILE_SIZE constant."""
        assert MAX_FILE_SIZE == 10 * 1024 * 1024  # 10MB
    
    def test_allowed_extensions_constant(self):
        """Test ALLOWED_EXTENSIONS constant."""
        assert ALLOWED_EXTENSIONS == {".pdf", ".docx"}
        assert len(ALLOWED_EXTENSIONS) == 2
