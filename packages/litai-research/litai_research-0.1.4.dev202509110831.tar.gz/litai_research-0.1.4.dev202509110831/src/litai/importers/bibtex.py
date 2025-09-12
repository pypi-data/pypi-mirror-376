"""BibTeX import functionality for LitAI."""

import hashlib
import re
import shutil
from pathlib import Path
from typing import Any

import arxiv  # type: ignore[import-untyped]
import bibtexparser
import httpx
import pdf2doi  # type: ignore[import-untyped]
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

from ..database import Database
from ..models import Paper
from ..utils.logger import get_logger

logger = get_logger(__name__)


def extract_arxiv_id(text: str) -> str | None:
    """Extract arXiv ID from URL or text.

    Args:
        text: Text that might contain an arXiv ID

    Returns:
        ArXiv ID if found, None otherwise
    """
    if not text:
        return None

    # Match arxiv URLs and IDs
    patterns = [
        r"arxiv\.org/abs/(\d{4}\.\d{4,5}v?\d*)",
        r"arxiv\.org/pdf/(\d{4}\.\d{4,5}v?\d*)",
        r"(\d{4}\.\d{4,5}v?\d*)",  # Just the ID
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def extract_doi(text: str) -> str | None:
    """Extract DOI from URL or text.

    Args:
        text: Text that might contain a DOI

    Returns:
        DOI if found, None otherwise
    """
    if not text:
        return None

    # DOI patterns
    patterns = [
        r"doi\.org/(10\.\d{4,9}/[-._;()/:\w]+)",
        r"doi:\s*(10\.\d{4,9}/[-._;()/:\w]+)",
        r"(10\.\d{4,9}/[-._;()/:\w]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def generate_paper_id(entry: dict[str, Any]) -> str:
    """Generate a unique paper ID from BibTeX entry.

    Priority order:
    1. ArXiv ID
    2. DOI
    3. Hash of citation key

    Args:
        entry: BibTeX entry dict

    Returns:
        Generated paper ID
    """
    # Try to extract arXiv ID
    url = entry.get("url", "")
    if arxiv_id := extract_arxiv_id(url):
        return f"arxiv:{arxiv_id}"

    # Try DOI from doi field or URL
    doi = entry.get("doi") or extract_doi(url)
    if doi:
        return f"doi:{doi}"

    # Fallback to hash of citation key
    citation_key = entry.get("ID", "unknown")
    hash_val = hashlib.md5(citation_key.encode()).hexdigest()[:12]
    return f"bib:{hash_val}"


def clean_latex(text: str) -> str:
    """Clean LaTeX formatting from text.

    Args:
        text: Text with potential LaTeX formatting

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove common LaTeX commands
    text = re.sub(r"\\textit{([^}]*)}", r"\1", text)
    text = re.sub(r"\\textbf{([^}]*)}", r"\1", text)
    text = re.sub(r"\\emph{([^}]*)}", r"\1", text)
    text = re.sub(r"\\cite{[^}]*}", "", text)
    text = re.sub(r"\\[a-zA-Z]+{([^}]*)}", r"\1", text)

    # Remove braces
    text = text.replace("{", "").replace("}", "")

    # Clean up whitespace
    return " ".join(text.split())


def parse_authors(author_str: str) -> list[str]:
    """Parse author string into list of names.

    Args:
        author_str: Author string from BibTeX

    Returns:
        List of author names
    """
    if not author_str:
        return []

    # Split by 'and'
    authors = author_str.split(" and ")

    # Clean up each author
    cleaned_authors = []
    for author in authors:
        author = author.strip()
        if not author:
            continue

        # Handle "Last, First" format
        if "," in author:
            parts = author.split(",", 1)
            author = f"{parts[1].strip()} {parts[0].strip()}"

        cleaned_authors.append(author)

    return cleaned_authors


def bibtex_to_paper(entry: dict[str, Any]) -> Paper | None:
    """Convert BibTeX entry to Paper object.

    Args:
        entry: BibTeX entry dict

    Returns:
        Paper object or None if required fields missing
    """
    # Check required fields
    if not all(key in entry for key in ["title", "author", "year"]):
        logger.warning("Missing required fields", entry_id=entry.get("ID", "unknown"))
        return None

    try:
        # Clean and extract fields
        paper_id = generate_paper_id(entry)
        title = clean_latex(entry["title"])
        authors = parse_authors(entry["author"])
        year = int(entry["year"])
        abstract = clean_latex(entry.get("abstract", ""))

        # Extract identifiers
        url = entry.get("url", "")
        arxiv_id = extract_arxiv_id(url)
        doi = entry.get("doi") or extract_doi(url)

        # Try to get venue from journal or booktitle
        venue = entry.get("journal") or entry.get("booktitle")
        if venue:
            venue = clean_latex(venue)

        # Generate arXiv PDF URL if we have arXiv ID
        open_access_pdf_url = None
        if arxiv_id:
            open_access_pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        return Paper(
            paper_id=paper_id,
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            arxiv_id=arxiv_id,
            doi=doi,
            citation_count=0,  # Will be enriched later
            tldr=None,  # Will be generated later
            venue=venue,
            open_access_pdf_url=open_access_pdf_url,
            citation_key=entry.get("ID"),
        )

    except Exception as e:
        logger.error(
            "Error converting BibTeX entry",
            entry_id=entry.get("ID", "unknown"),
            error=str(e),
        )
        return None


def parse_bibtex_file(file_path: Path) -> list[Paper]:
    """Parse BibTeX file and return list of Paper objects.

    Args:
        file_path: Path to BibTeX file

    Returns:
        List of successfully parsed Paper objects
    """
    papers = []

    try:
        with open(file_path, encoding="utf-8") as bibfile:
            parser = BibTexParser()
            parser.customization = convert_to_unicode
            bib_database = bibtexparser.load(bibfile, parser=parser)

            logger.info(
                "Parsing BibTeX file",
                path=str(file_path),
                entry_count=len(bib_database.entries),
            )

            for entry in bib_database.entries:
                paper = bibtex_to_paper(entry)
                if paper:
                    papers.append(paper)
                    logger.debug(
                        "Parsed paper",
                        paper_id=paper.paper_id,
                        title=paper.title[:50] + "...",
                    )

            logger.info(
                "BibTeX parsing complete",
                parsed=len(papers),
                skipped=len(bib_database.entries) - len(papers),
            )

    except Exception as e:
        logger.error("Error parsing BibTeX file", path=str(file_path), error=str(e))
        raise

    return papers


# PDF Import Functions

async def fetch_from_crossref(doi: str) -> Paper | None:
    """Fetch metadata from CrossRef API using DOI.
    
    Args:
        doi: DOI to look up
        
    Returns:
        Paper object or None if not found/error
    """
    if not doi:
        logger.debug("No DOI provided to fetch_from_crossref")
        return None
        
    logger.debug("Starting CrossRef API request", doi=doi)
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.crossref.org/works/{doi}"
            logger.debug("Sending request to CrossRef", url=url)
            response = await client.get(url, timeout=10.0)
            
            if response.status_code != 200:
                logger.warning("CrossRef API error", doi=doi, status_code=response.status_code)
                return None
                
            logger.debug("CrossRef API response received", doi=doi, status_code=response.status_code)
            data = response.json()
            work = data.get("message")
            
            if not work:
                logger.warning("No message in CrossRef response", doi=doi)
                return None
                
            # Extract required fields
            title = work.get("title", [""])[0] if work.get("title") else ""
            if not title:
                logger.warning("No title found in CrossRef response", doi=doi)
                return None
            logger.debug("Extracted title from CrossRef", doi=doi, title=title[:50])
                
            # Extract authors
            authors = []
            for author in work.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                if family:
                    name = f"{given} {family}".strip()
                    authors.append(name)
                    
            if not authors:
                logger.warning("No authors found in CrossRef response", doi=doi)
                return None
            logger.debug("Extracted authors from CrossRef", doi=doi, author_count=len(authors))
                
            # Extract year from published date - try multiple date fields
            year = None
            for date_field in ["published-print", "published-online", "published", "issued"]:
                published = work.get(date_field)
                if published and "date-parts" in published:
                    date_parts = published["date-parts"]
                    if date_parts and date_parts[0] and date_parts[0][0]:
                        year = date_parts[0][0]
                        logger.debug("Found year in CrossRef field", doi=doi, field=date_field, year=year)
                        break
                    
            if not year:
                logger.warning("No year found in CrossRef response", doi=doi)
                return None
                
            # Extract optional fields
            abstract = work.get("abstract", "")
            venue = None
            if "container-title" in work and work["container-title"]:
                venue = work["container-title"][0]
            
            # Extract citation count if available (reference-count is how many papers this paper cites)
            # is-referenced-by-count is how many times this paper has been cited
            citation_count = work.get("is-referenced-by-count", 0)
                
            paper = Paper(
                paper_id=f"doi:{doi}",
                title=title,
                authors=authors,
                year=year,
                abstract=abstract,
                doi=doi,
                venue=venue,
                citation_count=citation_count,
                tldr=None,
            )
            
            logger.info("Successfully fetched paper from CrossRef", 
                doi=doi, 
                title=title[:50], 
                authors=len(authors),
                year=year,
                has_abstract=bool(abstract),
                venue=venue,
                citations=citation_count,
            )
            return paper
            
    except httpx.TimeoutException:
        logger.error("CrossRef API timeout", doi=doi)
        return None
    except httpx.NetworkError as e:
        logger.error("Network error fetching from CrossRef", doi=doi, error=str(e))
        return None
    except Exception as e:
        logger.error("Unexpected error fetching from CrossRef", doi=doi, error=str(e), error_type=type(e).__name__)
        return None


def is_arxiv_doi(doi: str) -> bool:
    """Check if a DOI is from arXiv.
    
    Args:
        doi: DOI to check
        
    Returns:
        True if arXiv DOI, False otherwise
    """
    if not doi:
        return False
    return doi.startswith("10.48550/arXiv.")


def extract_arxiv_id_from_doi(doi: str) -> str | None:
    """Extract arXiv ID from arXiv DOI.
    
    Args:
        doi: arXiv DOI (e.g., "10.48550/arXiv.2107.08430v1")
        
    Returns:
        arXiv ID (e.g., "2107.08430v1") or None if not arXiv DOI
    """
    if not is_arxiv_doi(doi):
        return None
        
    # Extract ID after "arXiv."
    match = re.search(r"arXiv\.([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)", doi)
    if match:
        return match.group(1)
        
    return None


def convert_arxiv_to_paper(arxiv_result: Any) -> Paper | None:
    """Convert arXiv search result to Paper object.
    
    Args:
        arxiv_result: Result from arxiv package search
        
    Returns:
        Paper object or None if conversion fails
    """
    try:
        # Extract arXiv ID from entry_id
        entry_id = arxiv_result.entry_id
        arxiv_id = extract_arxiv_id(entry_id)
        if not arxiv_id:
            logger.warning("Could not extract arXiv ID", entry_id=entry_id)
            return None
            
        # Extract authors
        authors = []
        for author in arxiv_result.authors:
            if hasattr(author, 'name'):
                authors.append(str(author.name))
            else:
                authors.append(str(author))
        
        # Extract year from published date
        year = arxiv_result.published.year
        
        paper = Paper(
            paper_id=f"arxiv:{arxiv_id}",
            title=arxiv_result.title,
            authors=authors,
            year=year,
            abstract=arxiv_result.summary,
            arxiv_id=arxiv_id,
            open_access_pdf_url=arxiv_result.pdf_url,
            citation_count=0,
            tldr=None,
        )
        
        logger.info("Converted arXiv result to paper", arxiv_id=arxiv_id, title=paper.title[:50])
        return paper
        
    except Exception as e:
        logger.error("Error converting arXiv result", error=str(e))
        return None


async def extract_metadata_from_pdf(pdf_path: Path) -> Paper | None:
    """Extract metadata from PDF using pdf2doi and route to appropriate API.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Paper object or None if extraction fails
    """
    if not pdf_path.exists():
        logger.warning("PDF file not found", path=str(pdf_path))
        return None
        
    logger.info("Starting PDF metadata extraction", path=str(pdf_path), size_kb=pdf_path.stat().st_size / 1024)
    try:
        # Extract DOI/identifier from PDF
        logger.debug("Calling pdf2doi to extract identifier", path=str(pdf_path))
        result = pdf2doi.pdf2doi(str(pdf_path))
        
        if not result or "identifier" not in result:
            logger.warning("No identifier found in PDF", path=str(pdf_path), result=result)
            return None
            
        identifier = result["identifier"]
        logger.info("Found identifier in PDF", path=str(pdf_path), identifier=identifier, identifier_type="arXiv" if is_arxiv_doi(identifier) else "DOI")
        
        # Check if it's an arXiv DOI
        if is_arxiv_doi(identifier):
            arxiv_id = extract_arxiv_id_from_doi(identifier)
            if not arxiv_id:
                logger.warning("Could not extract arXiv ID from DOI", doi=identifier)
                return None
                
            # Search arXiv directly
            logger.info("Routing to arXiv API for metadata", arxiv_id=arxiv_id)
            client = arxiv.Client()
            search = arxiv.Search(id_list=[arxiv_id])
            logger.debug("Querying arXiv API", arxiv_id=arxiv_id)
            results = list(client.results(search))
            
            if not results:
                logger.warning("arXiv paper not found", arxiv_id=arxiv_id)
                return None
            
            logger.debug("Found arXiv paper", arxiv_id=arxiv_id, result_count=len(results))
            return convert_arxiv_to_paper(results[0])
        # Regular DOI - use CrossRef
        logger.info("Routing to CrossRef API for metadata", doi=identifier)
        return await fetch_from_crossref(identifier)
            
    except Exception as e:
        logger.error("Error extracting metadata from PDF", 
            path=str(pdf_path), 
            error=str(e),
            error_type=type(e).__name__,
        )
        return None


async def import_pdfs(
    pdf_paths: list[Path],
    db: Database,
    pdf_storage_dir: Path,
) -> tuple[int, int, int]:
    """Import PDFs with duplicate detection and storage.
    
    Args:
        pdf_paths: List of PDF file paths to import
        db: Database instance
        pdf_storage_dir: Directory to store PDFs
        
    Returns:
        Tuple of (added, skipped, failed) counts
    """
    added = 0
    skipped = 0
    failed = 0
    
    logger.info("Starting PDF import batch", pdf_count=len(pdf_paths), storage_dir=str(pdf_storage_dir))
    
    # Ensure storage directory exists
    pdf_storage_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("PDF storage directory ready", path=str(pdf_storage_dir))
    
    for pdf_path in pdf_paths:
        try:
            if not pdf_path.exists():
                logger.warning("PDF file not found", path=str(pdf_path))
                failed += 1
                continue
                
            logger.info("Processing PDF", 
                path=str(pdf_path),
                filename=pdf_path.name,
                progress=f"{pdf_paths.index(pdf_path) + 1}/{len(pdf_paths)}",
            )
            
            # Extract metadata
            paper = await extract_metadata_from_pdf(pdf_path)
            if not paper:
                logger.warning("Could not extract metadata from PDF", 
                    path=str(pdf_path),
                    reason="No metadata extracted",
                )
                failed += 1
                continue
                
            # Check for duplicates
            logger.debug("Checking for duplicates", paper_id=paper.paper_id, doi=paper.doi, arxiv_id=paper.arxiv_id)
            existing_paper = None
            if paper.doi:
                existing_paper = db.get_paper_by_doi(paper.doi)
                if existing_paper:
                    logger.debug("Found existing paper by DOI", doi=paper.doi, existing_id=existing_paper.paper_id)
            elif paper.arxiv_id:
                existing_paper = db.get_paper_by_arxiv_id(paper.arxiv_id)
                if existing_paper:
                    logger.debug("Found existing paper by arXiv ID", arxiv_id=paper.arxiv_id, existing_id=existing_paper.paper_id)
                
            if existing_paper:
                logger.info(
                    "Paper already in collection, skipping import",
                    paper_id=paper.paper_id,
                    existing_id=existing_paper.paper_id,
                    title=paper.title[:50],
                    path=str(pdf_path),
                )
                skipped += 1
                continue
                
            # Copy PDF to storage directory
            # Replace colons with underscores for filesystem compatibility
            safe_filename = paper.paper_id.replace(":", "_").replace("/", "_")
            dest_path = pdf_storage_dir / f"{safe_filename}.pdf"
            logger.debug("Copying PDF to storage", src=str(pdf_path), dest=str(dest_path))
            try:
                # Ensure parent directory exists (in case paper_id has slashes)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(pdf_path, dest_path)
                # Get file size after copy
                file_size_kb = dest_path.stat().st_size / 1024 if dest_path.exists() else 0
                logger.info("PDF copied to storage", 
                    src=str(pdf_path), 
                    dest=str(dest_path),
                    size_kb=file_size_kb,
                )
            except Exception as e:
                logger.error("Failed to copy PDF", 
                    src=str(pdf_path), 
                    dest=str(dest_path), 
                    error=str(e),
                    error_type=type(e).__name__,
                )
                failed += 1
                continue
                
            # Add paper to database/collection
            logger.debug("Adding paper to collection", paper_id=paper.paper_id, title=paper.title[:50])
            try:
                success = db.add_paper(paper)
                if success:
                    logger.info("✓ Paper successfully added to collection", 
                        paper_id=paper.paper_id, 
                        title=paper.title[:50],
                        doi=paper.doi,
                        arxiv_id=paper.arxiv_id,
                        authors=len(paper.authors),
                        year=paper.year,
                    )
                    added += 1
                else:
                    logger.warning("Paper not added to collection (duplicate check failed?)", 
                        paper_id=paper.paper_id,
                        title=paper.title[:50],
                    )
                    # Remove the copied PDF since we didn't add the paper
                    dest_path.unlink(missing_ok=True)
                    logger.debug("Removed copied PDF since paper wasn't added", path=str(dest_path))
                    skipped += 1
            except Exception as e:
                logger.error("Database error adding paper to collection", 
                    paper_id=paper.paper_id, 
                    title=paper.title[:50],
                    error=str(e),
                    error_type=type(e).__name__,
                )
                # Remove the copied PDF since we couldn't add the paper
                dest_path.unlink(missing_ok=True)
                logger.debug("Removed copied PDF due to database error", path=str(dest_path))
                failed += 1
                continue
                
        except Exception as e:
            logger.error("Unexpected error processing PDF", 
                path=str(pdf_path), 
                error=str(e),
                error_type=type(e).__name__,
                traceback=True,  # This will include traceback in structured logs
            )
            failed += 1
            
    logger.info(
        "PDF import batch complete",
        total=len(pdf_paths),
        added_to_collection=added,
        skipped_duplicates=skipped,
        failed=failed,
        success_rate=f"{(added / len(pdf_paths) * 100):.1f}%" if pdf_paths else "N/A",
    )
    
    return added, skipped, failed
