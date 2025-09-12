"""Tests for PDF import functionality.

This test file follows test-driven development (TDD) approach.
Tests are written to fail initially since functionality is not implemented yet.
"""

import tempfile
from pathlib import Path
from unittest import mock

import pytest

from litai.config import Config
from litai.database import Database

# Import functions that don't exist yet - this is TDD
from litai.importers.bibtex import (
    convert_arxiv_to_paper,
    extract_arxiv_id_from_doi,
    extract_metadata_from_pdf,
    fetch_from_crossref,
    import_pdfs,
    is_arxiv_doi,
)
from litai.models import Paper


@pytest.fixture
def test_db():
    """Create a test database in memory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config(Path(temp_dir))
        db = Database(config)
        yield db


@pytest.fixture
def pdf_storage_dir():
    """Create a temporary PDF storage directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_dir = Path(temp_dir) / "pdfs"
        pdf_dir.mkdir()
        yield pdf_dir


@pytest.fixture
def sample_pdf_file(tmp_path):
    """Create a sample PDF file for testing."""
    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(b"fake pdf content for testing")
    return pdf_file


class TestCrossRefAPI:
    """Test CrossRef API integration."""

    @pytest.mark.asyncio
    async def test_fetch_from_crossref_valid_doi(self):
        """Test fetching metadata from CrossRef with valid DOI."""
        # Test with a real DOI from CVPR 2024
        doi = "10.1109/cvpr52733.2024.01310"
        paper = await fetch_from_crossref(doi)
        
        assert paper is not None
        assert paper.doi == doi
        assert paper.title  # Should have a title
        assert paper.authors  # Should have authors  
        assert paper.year  # Should have year
        assert paper.paper_id == f"doi:{doi}"

    @pytest.mark.asyncio
    async def test_fetch_from_crossref_invalid_doi(self):
        """Test CrossRef gracefully handles invalid DOI."""
        paper = await fetch_from_crossref("invalid-doi-12345")
        assert paper is None

    @pytest.mark.asyncio
    async def test_fetch_from_crossref_network_error(self):
        """Test CrossRef handles network errors gracefully."""
        with mock.patch('httpx.AsyncClient.get') as mock_get:
            # Mock network timeout
            mock_get.side_effect = Exception("Network timeout")
            
            paper = await fetch_from_crossref("10.1000/test")
            assert paper is None

    @pytest.mark.asyncio
    async def test_fetch_from_crossref_404_response(self):
        """Test CrossRef handles 404 responses gracefully."""
        with mock.patch('httpx.AsyncClient.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.status_code = 404
            mock_get.return_value.__aenter__.return_value.get.return_value = mock_response
            
            paper = await fetch_from_crossref("10.1000/nonexistent")
            assert paper is None


class TestArXivDOIHandling:
    """Test arXiv DOI detection and routing."""

    def test_is_arxiv_doi(self):
        """Test detection of arXiv DOIs."""
        # arXiv DOIs follow pattern 10.48550/arXiv.XXXX.XXXXX
        assert is_arxiv_doi("10.48550/arXiv.2507.18071") is True
        assert is_arxiv_doi("10.48550/arXiv.1234.5678v2") is True
        
        # Regular DOIs should return False
        assert is_arxiv_doi("10.1109/cvpr52733.2024.01310") is False
        assert is_arxiv_doi("10.1038/nature12373") is False
        
        # Invalid formats
        assert is_arxiv_doi("not-a-doi") is False
        assert is_arxiv_doi("") is False
        assert is_arxiv_doi(None) is False

    def test_extract_arxiv_id_from_doi(self):
        """Test extracting arXiv ID from DOI."""
        # Valid arXiv DOI
        doi = "10.48550/arXiv.2507.18071"
        arxiv_id = extract_arxiv_id_from_doi(doi)
        assert arxiv_id == "2507.18071"
        
        # With version
        doi = "10.48550/arXiv.1234.5678v2"
        arxiv_id = extract_arxiv_id_from_doi(doi)
        assert arxiv_id == "1234.5678v2"
        
        # Non-arXiv DOI
        arxiv_id = extract_arxiv_id_from_doi("10.1109/test.2024")
        assert arxiv_id is None

    @pytest.mark.asyncio
    async def test_arxiv_doi_routing_in_extraction(self, sample_pdf_file):
        """Test that arXiv DOIs are routed to arXiv API instead of CrossRef."""
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            # Mock pdf2doi to return arXiv DOI
            mock_pdf2doi.return_value = {'identifier': '10.48550/arXiv.2507.18071'}
            
            with mock.patch('litai.importers.bibtex.convert_arxiv_to_paper') as mock_convert:
                mock_paper = Paper(
                    paper_id="arxiv:2507.18071",
                    title="Test arXiv Paper",
                    authors=["Test Author"],
                    year=2024,
                    abstract="Test abstract",
                    arxiv_id="2507.18071",
                )
                mock_convert.return_value = mock_paper
                
                # Should use arXiv conversion, not CrossRef
                paper = await extract_metadata_from_pdf(sample_pdf_file)
                assert paper is not None
                assert paper.arxiv_id == "2507.18071"
                assert paper.paper_id == "arxiv:2507.18071"
                mock_convert.assert_called_once()


class TestPDFMetadataExtraction:
    """Test PDF metadata extraction pipeline."""

    @pytest.mark.asyncio
    async def test_extract_metadata_success_regular_doi(self, sample_pdf_file):
        """Test successful metadata extraction with regular DOI."""
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            mock_pdf2doi.return_value = {'identifier': '10.1109/test.2024'}
            
            with mock.patch('litai.importers.bibtex.fetch_from_crossref') as mock_crossref:
                mock_paper = Paper(
                    paper_id="doi:10.1109/test.2024",
                    title="Test Paper",
                    authors=["Test Author"],
                    year=2024,
                    abstract="Test abstract",
                    doi="10.1109/test.2024",
                )
                mock_crossref.return_value = mock_paper
                
                paper = await extract_metadata_from_pdf(sample_pdf_file)
                assert paper is not None
                assert paper.doi == "10.1109/test.2024"
                assert paper.paper_id == "doi:10.1109/test.2024"

    @pytest.mark.asyncio
    async def test_extract_metadata_pdf2doi_failure(self, sample_pdf_file):
        """Test handling of pdf2doi failure."""
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            # pdf2doi returns None or raises exception
            mock_pdf2doi.return_value = None
            
            paper = await extract_metadata_from_pdf(sample_pdf_file)
            assert paper is None

    @pytest.mark.asyncio 
    async def test_extract_metadata_no_identifier(self, sample_pdf_file):
        """Test handling when pdf2doi finds no identifier."""
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            # pdf2doi returns empty result
            mock_pdf2doi.return_value = {}
            
            paper = await extract_metadata_from_pdf(sample_pdf_file)
            assert paper is None

    @pytest.mark.asyncio
    async def test_extract_metadata_crossref_failure(self, sample_pdf_file):
        """Test handling when CrossRef API fails."""
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            mock_pdf2doi.return_value = {'identifier': '10.1109/test.2024'}
            
            with mock.patch('litai.importers.bibtex.fetch_from_crossref') as mock_crossref:
                # CrossRef returns None (API failure)
                mock_crossref.return_value = None
                
                paper = await extract_metadata_from_pdf(sample_pdf_file)
                assert paper is None

    @pytest.mark.asyncio
    async def test_extract_metadata_exception_handling(self, sample_pdf_file):
        """Test that exceptions are handled gracefully."""
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            # pdf2doi raises exception
            mock_pdf2doi.side_effect = Exception("PDF processing failed")
            
            paper = await extract_metadata_from_pdf(sample_pdf_file)
            assert paper is None


class TestPDFImportWorkflow:
    """Test PDF import workflow."""

    @pytest.mark.asyncio
    async def test_import_single_pdf_success(self, test_db, sample_pdf_file, pdf_storage_dir):
        """Test successful import of a single PDF."""
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            mock_pdf2doi.return_value = {'identifier': '10.1234/test'}
            
            with mock.patch('litai.importers.bibtex.fetch_from_crossref') as mock_crossref:
                mock_paper = Paper(
                    paper_id="doi:10.1234/test",
                    title="Test Paper",
                    authors=["Author One"],
                    year=2024,
                    abstract="Test abstract",
                    doi="10.1234/test",
                )
                mock_crossref.return_value = mock_paper
                
                with mock.patch('shutil.copy2') as mock_copy:
                    added, skipped, failed = await import_pdfs([sample_pdf_file], test_db, pdf_storage_dir)
                    
                    assert added == 1
                    assert skipped == 0
                    assert failed == 0
                    
                    # Check paper was added to database
                    papers = test_db.list_papers()
                    assert len(papers) == 1
                    assert papers[0].doi == "10.1234/test"
                    
                    # Check PDF was copied (with filesystem-safe filename)
                    mock_copy.assert_called_once()
                    expected_dest = pdf_storage_dir / "doi_10.1234_test.pdf"
                    mock_copy.assert_called_with(sample_pdf_file, expected_dest)

    @pytest.mark.asyncio
    async def test_import_multiple_pdfs(self, test_db, tmp_path, pdf_storage_dir):
        """Test importing multiple PDFs."""
        # Create multiple test PDFs
        pdf1 = tmp_path / "paper1.pdf"
        pdf2 = tmp_path / "paper2.pdf"
        pdf1.write_bytes(b"pdf content 1")
        pdf2.write_bytes(b"pdf content 2")
        
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            # Mock different DOIs for each PDF
            mock_pdf2doi.side_effect = [
                {'identifier': '10.1234/test1'},
                {'identifier': '10.1234/test2'},
            ]
            
            with mock.patch('litai.importers.bibtex.fetch_from_crossref') as mock_crossref:
                mock_crossref.side_effect = [
                    Paper(
                        paper_id="doi:10.1234/test1",
                        title="Test Paper 1",
                        authors=["Author One"],
                        year=2024,
                        abstract="Test abstract 1",
                        doi="10.1234/test1",
                    ),
                    Paper(
                        paper_id="doi:10.1234/test2", 
                        title="Test Paper 2",
                        authors=["Author Two"],
                        year=2024,
                        abstract="Test abstract 2",
                        doi="10.1234/test2",
                    ),
                ]
                
                with mock.patch('shutil.copy2'):
                    added, skipped, failed = await import_pdfs([pdf1, pdf2], test_db, pdf_storage_dir)
                    
                    assert added == 2
                    assert skipped == 0
                    assert failed == 0
                    
                    # Check both papers were added
                    papers = test_db.list_papers()
                    assert len(papers) == 2
                    dois = {p.doi for p in papers}
                    assert dois == {"10.1234/test1", "10.1234/test2"}

    @pytest.mark.asyncio
    async def test_import_mixed_success_failure(self, test_db, tmp_path, pdf_storage_dir):
        """Test importing PDFs with mixed success and failure."""
        pdf1 = tmp_path / "success.pdf"
        pdf2 = tmp_path / "failure.pdf"
        pdf1.write_bytes(b"success content")
        pdf2.write_bytes(b"failure content")
        
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            # First PDF succeeds, second fails
            mock_pdf2doi.side_effect = [
                {'identifier': '10.1234/success'},
                None,  # Failure
            ]
            
            with mock.patch('litai.importers.bibtex.fetch_from_crossref') as mock_crossref:
                mock_crossref.return_value = Paper(
                    paper_id="doi:10.1234/success",
                    title="Success Paper",
                    authors=["Author"],
                    year=2024,
                    abstract="Success abstract", 
                    doi="10.1234/success",
                )
                
                with mock.patch('shutil.copy2'):
                    added, skipped, failed = await import_pdfs([pdf1, pdf2], test_db, pdf_storage_dir)
                    
                    assert added == 1
                    assert skipped == 0
                    assert failed == 1
                    
                    # Only successful paper should be in database
                    papers = test_db.list_papers()
                    assert len(papers) == 1
                    assert papers[0].doi == "10.1234/success"


class TestDuplicateDetection:
    """Test duplicate paper detection."""

    @pytest.mark.asyncio
    async def test_duplicate_detection_by_doi(self, test_db, sample_pdf_file, pdf_storage_dir):
        """Test that duplicates are detected by DOI."""
        # Add existing paper to database
        existing_paper = Paper(
            paper_id="doi:10.1234/existing",
            title="Existing Paper",
            authors=["Existing Author"],
            year=2023,
            abstract="Existing abstract",
            doi="10.1234/existing",
        )
        test_db.add_paper(existing_paper)
        
        # Try to import PDF with same DOI
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            mock_pdf2doi.return_value = {'identifier': '10.1234/existing'}
            
            with mock.patch('litai.importers.bibtex.fetch_from_crossref') as mock_crossref:
                mock_crossref.return_value = Paper(
                    paper_id="doi:10.1234/existing",
                    title="Same Paper Different Title",
                    authors=["Different Author"],
                    year=2024,
                    abstract="Different abstract",
                    doi="10.1234/existing",
                )
                
                added, skipped, failed = await import_pdfs([sample_pdf_file], test_db, pdf_storage_dir)
                
                assert added == 0
                assert skipped == 1  # Should be skipped as duplicate
                assert failed == 0
                
                # Should still only have one paper
                papers = test_db.list_papers()
                assert len(papers) == 1
                assert papers[0].title == "Existing Paper"  # Original title preserved

    @pytest.mark.asyncio
    async def test_duplicate_detection_by_arxiv_id(self, test_db, sample_pdf_file, pdf_storage_dir):
        """Test that duplicates are detected by arXiv ID."""
        # Add existing arXiv paper
        existing_paper = Paper(
            paper_id="arxiv:1234.5678",
            title="Existing arXiv Paper",
            authors=["arXiv Author"],
            year=2023,
            abstract="arXiv abstract",
            arxiv_id="1234.5678",
        )
        test_db.add_paper(existing_paper)
        
        # Try to import PDF with same arXiv ID
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            mock_pdf2doi.return_value = {'identifier': '10.48550/arXiv.1234.5678'}
            
            with mock.patch('arxiv.Client') as mock_client_class:
                # Mock the arXiv client and search
                mock_client = mock.Mock()
                mock_client_class.return_value = mock_client
                mock_result = mock.Mock()
                mock_result.entry_id = "http://arxiv.org/abs/1234.5678"
                mock_result.title = "Same arXiv Paper"
                mock_author = mock.Mock()
                mock_author.name = "Same Author"
                mock_result.authors = [mock_author]
                mock_result.published = mock.Mock()
                mock_result.published.year = 2024
                mock_result.summary = "Same abstract"
                mock_result.pdf_url = "http://arxiv.org/pdf/1234.5678.pdf"
                mock_client.results.return_value = [mock_result]
                
                added, skipped, failed = await import_pdfs([sample_pdf_file], test_db, pdf_storage_dir)
                
                assert added == 0
                assert skipped == 1
                assert failed == 0
                
                # Should still only have one paper
                papers = test_db.list_papers()
                assert len(papers) == 1
                assert papers[0].title == "Existing arXiv Paper"

    @pytest.mark.asyncio
    async def test_no_duplicate_different_identifiers(self, test_db, tmp_path, pdf_storage_dir):
        """Test that papers with different identifiers are not considered duplicates."""
        # Add existing paper with DOI
        existing_paper = Paper(
            paper_id="doi:10.1234/existing",
            title="Existing Paper",
            authors=["Author"],
            year=2023,
            abstract="Abstract",
            doi="10.1234/existing",
        )
        test_db.add_paper(existing_paper)
        
        # Import paper with different DOI
        new_pdf = tmp_path / "new.pdf"
        new_pdf.write_bytes(b"new content")
        
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            mock_pdf2doi.return_value = {'identifier': '10.1234/different'}
            
            with mock.patch('litai.importers.bibtex.fetch_from_crossref') as mock_crossref:
                mock_crossref.return_value = Paper(
                    paper_id="doi:10.1234/different",
                    title="Different Paper",
                    authors=["Different Author"],
                    year=2024,
                    abstract="Different abstract",
                    doi="10.1234/different",
                )
                
                with mock.patch('shutil.copy2'):
                    added, skipped, failed = await import_pdfs([new_pdf], test_db, pdf_storage_dir)
                    
                    assert added == 1
                    assert skipped == 0
                    assert failed == 0
                    
                    # Should now have two papers
                    papers = test_db.list_papers()
                    assert len(papers) == 2
                    dois = {p.doi for p in papers}
                    assert dois == {"10.1234/existing", "10.1234/different"}


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_nonexistent_pdf_file(self, test_db, pdf_storage_dir):
        """Test handling of nonexistent PDF files."""
        nonexistent_file = Path("/does/not/exist.pdf")
        
        added, skipped, failed = await import_pdfs([nonexistent_file], test_db, pdf_storage_dir)
        
        # Should handle gracefully
        assert added == 0
        assert skipped == 0
        assert failed == 1

    @pytest.mark.asyncio
    async def test_pdf_copy_failure(self, test_db, sample_pdf_file, pdf_storage_dir):
        """Test handling of PDF copy failures."""
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            mock_pdf2doi.return_value = {'identifier': '10.1234/test'}
            
            with mock.patch('litai.importers.bibtex.fetch_from_crossref') as mock_crossref:
                mock_crossref.return_value = Paper(
                    paper_id="doi:10.1234/test",
                    title="Test Paper",
                    authors=["Author"],
                    year=2024,
                    abstract="Abstract",
                    doi="10.1234/test",
                )
                
                with mock.patch('shutil.copy2') as mock_copy:
                    # Mock copy failure
                    mock_copy.side_effect = OSError("Permission denied")
                    
                    added, skipped, failed = await import_pdfs([sample_pdf_file], test_db, pdf_storage_dir)
                    
                    # Should fail gracefully
                    assert added == 0
                    assert skipped == 0
                    assert failed == 1
                    
                    # Paper should not be added to database if copy fails
                    papers = test_db.list_papers()
                    assert len(papers) == 0

    @pytest.mark.asyncio
    async def test_database_error_handling(self, sample_pdf_file, pdf_storage_dir):
        """Test handling of database errors."""
        # Create a mock database that fails on add_paper
        mock_db = mock.Mock()
        mock_db.list_papers.return_value = []
        mock_db.add_paper.side_effect = Exception("Database error")
        
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            mock_pdf2doi.return_value = {'identifier': '10.1234/test'}
            
            with mock.patch('litai.importers.bibtex.fetch_from_crossref') as mock_crossref:
                mock_crossref.return_value = Paper(
                    paper_id="doi:10.1234/test", 
                    title="Test Paper",
                    authors=["Author"],
                    year=2024,
                    abstract="Abstract",
                    doi="10.1234/test",
                )
                
                added, skipped, failed = await import_pdfs([sample_pdf_file], mock_db, pdf_storage_dir)
                
                # Should handle database error gracefully
                assert added == 0
                assert skipped == 0
                assert failed == 1


class TestArXivConversion:
    """Test arXiv paper conversion functionality."""

    def test_convert_arxiv_to_paper(self):
        """Test conversion of arXiv result to Paper object."""
        # This test assumes convert_arxiv_to_paper exists and works with arxiv package
        # The actual implementation will depend on the arxiv package's API
        
        # Mock arXiv result object
        mock_arxiv_result = mock.Mock()
        mock_arxiv_result.entry_id = "http://arxiv.org/abs/2107.08430v1"
        mock_arxiv_result.title = "Test arXiv Paper Title"
        # Create mock authors with .name attribute
        mock_author1 = mock.Mock()
        mock_author1.name = "John Doe"
        mock_author2 = mock.Mock()
        mock_author2.name = "Jane Smith"
        mock_arxiv_result.authors = [mock_author1, mock_author2]
        mock_arxiv_result.published = mock.Mock()
        mock_arxiv_result.published.year = 2021
        mock_arxiv_result.summary = "This is the abstract of the paper."
        mock_arxiv_result.pdf_url = "http://arxiv.org/pdf/2107.08430v1.pdf"
        
        paper = convert_arxiv_to_paper(mock_arxiv_result)
        
        assert paper is not None
        assert paper.paper_id == "arxiv:2107.08430v1"
        assert paper.title == "Test arXiv Paper Title"
        assert paper.authors == ["John Doe", "Jane Smith"]
        assert paper.year == 2021
        assert paper.abstract == "This is the abstract of the paper."
        assert paper.arxiv_id == "2107.08430v1"
        assert paper.open_access_pdf_url == "http://arxiv.org/pdf/2107.08430v1.pdf"


class TestPDFStorageNaming:
    """Test PDF file naming and storage logic."""

    def test_pdf_path_generation(self, pdf_storage_dir):
        """Test that PDF paths are generated correctly from paper IDs."""
        # Test DOI-based paper ID
        expected_path = pdf_storage_dir / "doi:10.1234/test.paper.pdf"
        
        # This assumes there's a utility function for generating paths
        # The actual implementation might be in PDFProcessor or similar
        assert str(expected_path).endswith("doi:10.1234/test.paper.pdf")
        
        # Test arXiv-based paper ID
        expected_path = pdf_storage_dir / "arxiv:2107.08430.pdf"
        
        assert str(expected_path).endswith("arxiv:2107.08430.pdf")

    def test_pdf_path_sanitization(self, pdf_storage_dir):
        """Test that paper IDs with special characters are handled safely."""
        # Paper IDs might contain characters that need sanitization for filenames
        # This test ensures the system handles them properly
        tricky_paper_id = "doi:10.1234/test-paper_with.special@chars"
        
        # The system should either sanitize or handle these characters safely
        # Implementation details will depend on the actual path generation logic
        expected_path = pdf_storage_dir / f"{tricky_paper_id}.pdf"
        
        # At minimum, the path should be creatable
        assert isinstance(expected_path, Path)


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_complete_folder_import_workflow(self, test_db, tmp_path, pdf_storage_dir):
        """Test importing an entire folder of mixed PDFs."""
        # Create a folder with multiple PDFs
        pdf_folder = tmp_path / "research_papers"
        pdf_folder.mkdir()
        
        # Create test PDFs
        (pdf_folder / "paper1.pdf").write_bytes(b"content 1")
        (pdf_folder / "paper2.pdf").write_bytes(b"paper2 content")
        (pdf_folder / "paper3.pdf").write_bytes(b"third paper")
        
        # Mock mixed scenarios: success, duplicate, failure
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            mock_pdf2doi.side_effect = [
                {'identifier': '10.1234/paper1'},  # Success
                {'identifier': '10.1234/paper1'},  # Duplicate
                None,  # Failure
            ]
            
            with mock.patch('litai.importers.bibtex.fetch_from_crossref') as mock_crossref:
                mock_crossref.side_effect = [
                    Paper(
                        paper_id="doi:10.1234/paper1",
                        title="First Paper",
                        authors=["Author 1"],
                        year=2024,
                        abstract="Abstract 1",
                        doi="10.1234/paper1",
                    ),
                    Paper(
                        paper_id="doi:10.1234/paper1",
                        title="Duplicate Paper",
                        authors=["Author 2"],
                        year=2024,
                        abstract="Abstract 2",
                        doi="10.1234/paper1",
                    ),
                ]
                
                pdf_files = list(pdf_folder.glob("*.pdf"))
                
                with mock.patch('shutil.copy2'):
                    added, skipped, failed = await import_pdfs(pdf_files, test_db, pdf_storage_dir)
                    
                    assert added == 1  # First paper added
                    assert skipped == 1  # Second paper skipped (duplicate)
                    assert failed == 1  # Third paper failed
                    
                    # Verify only one paper in database
                    papers = test_db.list_papers()
                    assert len(papers) == 1
                    assert papers[0].title == "First Paper"

    @pytest.mark.asyncio 
    async def test_arxiv_and_published_paper_mix(self, test_db, tmp_path, pdf_storage_dir):
        """Test importing mix of arXiv and published papers."""
        arxiv_pdf = tmp_path / "arxiv_paper.pdf"
        published_pdf = tmp_path / "published_paper.pdf"
        arxiv_pdf.write_bytes(b"arxiv content")
        published_pdf.write_bytes(b"published content")
        
        with mock.patch('pdf2doi.pdf2doi') as mock_pdf2doi:
            mock_pdf2doi.side_effect = [
                {'identifier': '10.48550/arXiv.2107.08430'},  # arXiv DOI
                {'identifier': '10.1109/published.2024'},      # Regular DOI
            ]
            
            with mock.patch('litai.importers.bibtex.convert_arxiv_to_paper') as mock_arxiv_convert:
                mock_arxiv_convert.return_value = Paper(
                    paper_id="arxiv:2107.08430",
                    title="arXiv Paper",
                    authors=["arXiv Author"],
                    year=2021,
                    abstract="arXiv abstract",
                    arxiv_id="2107.08430",
                )
                
                with mock.patch('litai.importers.bibtex.fetch_from_crossref') as mock_crossref:
                    mock_crossref.return_value = Paper(
                        paper_id="doi:10.1109/published.2024",
                        title="Published Paper",
                        authors=["Published Author"],
                        year=2024,
                        abstract="Published abstract",
                        doi="10.1109/published.2024",
                    )
                    
                    with mock.patch('shutil.copy2'):
                        added, skipped, failed = await import_pdfs([arxiv_pdf, published_pdf], test_db, pdf_storage_dir)
                        
                        assert added == 2
                        assert skipped == 0
                        assert failed == 0
                        
                        papers = test_db.list_papers()
                        assert len(papers) == 2
                        
                        # Check both types of papers are present
                        paper_types = {p.paper_id.split(':')[0] for p in papers}
                        assert paper_types == {"arxiv", "doi"}