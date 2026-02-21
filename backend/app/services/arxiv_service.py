"""arXiv API service for searching and downloading papers."""
import xml.etree.ElementTree as ET
import requests
import time
from typing import List, Optional, Dict
from datetime import datetime
from urllib.parse import urlencode

from app.models.arxiv import ArxivPaper


class ArxivService:
    """Service for interacting with arXiv API."""

    BASE_URL = "http://export.arxiv.org/api/query"
    PDF_BASE_URL = "http://arxiv.org/pdf"
    ABSTRACT_BASE_URL = "http://arxiv.org/abs"

    # arXiv API namespaces
    NAMESPACES = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ScholarLens/1.0 (https://scholarlens.app; mailto:contact@scholarlens.app)"
        })
        # Rate limiting: 1 request per 3 seconds
        self.last_request_time = 0
        self.min_request_interval = 3

    def _rate_limited_request(self, url: str, params: dict = None) -> requests.Response:
        """Make a rate-limited request to arXiv API."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        response = self.session.get(url, params=params, timeout=30)
        self.last_request_time = time.time()
        return response

    def search_papers(
        self,
        query: str,
        start: int = 0,
        max_results: int = 50,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> List[ArxivPaper]:
        """
        Search for papers on arXiv.

        Args:
            query: arXiv search query (e.g., "all:transformer", "cat:cs.CL")
            start: Start index for pagination
            max_results: Maximum number of results (max 2000)
            sort_by: Sort by "relevance", "lastUpdatedDate", or "submittedDate"
            sort_order: "ascending" or "descending"

        Returns:
            List of ArxivPaper objects
        """
        params = {
            "search_query": query,
            "start": start,
            "max_results": min(max_results, 2000),  # arXiv limit
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        response = self._rate_limited_request(self.BASE_URL, params)
        response.raise_for_status()

        return self._parse_atom_feed(response.text)

    def _parse_atom_feed(self, xml_content: str) -> List[ArxivPaper]:
        """Parse arXiv Atom feed XML into ArxivPaper objects."""
        papers = []

        try:
            root = ET.fromstring(xml_content.encode("utf-8"))

            for entry in root.findall("atom:entry", self.NAMESPACES):
                paper = self._parse_entry(entry)
                if paper:
                    papers.append(paper)

        except ET.ParseError as e:
            print(f"Failed to parse arXiv feed: {e}")

        return papers

    def _parse_entry(self, entry: ET.Element) -> Optional[ArxivPaper]:
        """Parse a single Atom entry into an ArxivPaper."""
        try:
            # Get arXiv ID from URL
            id_url = entry.find("atom:id", self.NAMESPACES)
            if id_url is None:
                return None

            arxiv_id = id_url.text.split("/abs/")[-1]
            if "v" in arxiv_id:  # Remove version suffix
                arxiv_id = arxiv_id.split("v")[0]

            # Get title
            title_elem = entry.find("atom:title", self.NAMESPACES)
            title = title_elem.text if title_elem else ""
            title = " ".join(title.split())  # Normalize whitespace

            # Get summary/abstract
            summary_elem = entry.find("atom:summary", self.NAMESPACES)
            summary = summary_elem.text if summary_elem else ""

            # Get authors
            authors = []
            for author in entry.findall("atom:author", self.NAMESPACES):
                name_elem = author.find("atom:name", self.NAMESPACES)
                if name_elem is not None:
                    authors.append(name_elem.text)

            # Get categories
            categories = []
            primary_category = ""
            for cat in entry.findall("atom:category", self.NAMESPACES):
                term = cat.get("term", "")
                if term:
                    categories.append(term)

            # Get primary category from arxiv:primary_category
            primary_elem = entry.find("arxiv:primary_category", self.NAMESPACES)
            if primary_elem is not None:
                primary_category = primary_elem.get("term", "")

            # Get published and updated dates
            published_elem = entry.find("atom:published", self.NAMESPACES)
            updated_elem = entry.find("atom:updated", self.NAMESPACES)

            published = self._parse_datetime(published_elem.text) if published_elem else None
            updated = self._parse_datetime(updated_elem.text) if updated_elem else None

            # Get links
            pdf_url = ""
            arxiv_url = f"{self.ABSTRACT_BASE_URL}/{arxiv_id}"

            for link in entry.findall("atom:link", self.NAMESPACES):
                href = link.get("href", "")
                link_type = link.get("type", "")
                title_attr = link.get("title", "")

                if link_type == "application/pdf":
                    pdf_url = href
                elif title_attr == "pdf":
                    pdf_url = href

            # Ensure PDF URL is set
            if not pdf_url:
                pdf_url = f"{self.PDF_BASE_URL}/{arxiv_id}.pdf"

            # Get DOI and journal reference if available
            doi = None
            journal_ref = None

            return ArxivPaper(
                id=arxiv_id,
                title=title,
                authors=authors,
                summary=summary,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                pdf_url=pdf_url,
                arxiv_url=arxiv_url,
                doi=doi,
                journal_ref=journal_ref,
            )

        except Exception as e:
            print(f"Failed to parse arXiv entry: {e}")
            return None

    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not dt_str:
            return None
        try:
            # Handle various ISO formats
            dt_str = dt_str.replace("Z", "+00:00")
            return datetime.fromisoformat(dt_str)
        except ValueError:
            return None

    def download_pdf(self, arxiv_id: str, pdf_url: str, save_path: str) -> bool:
        """
        Download PDF from arXiv.

        Args:
            arxiv_id: arXiv paper ID
            pdf_url: Direct PDF URL
            save_path: Path to save the PDF

        Returns:
            True if download successful
        """
        try:
            # Rate limit
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last)

            response = self.session.get(pdf_url, timeout=60, stream=True)
            response.raise_for_status()

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.last_request_time = time.time()
            return True

        except Exception as e:
            print(f"Failed to download PDF for {arxiv_id}: {e}")
            return False

    def get_paper_by_id(self, arxiv_id: str) -> Optional[ArxivPaper]:
        """Get a specific paper by arXiv ID."""
        query = f"id:{arxiv_id}"
        papers = self.search_papers(query, max_results=1)
        return papers[0] if papers else None

    @staticmethod
    def build_query(
        keywords: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        authors: Optional[List[str]] = None,
        title: Optional[str] = None,
        abstract: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> str:
        """
        Build arXiv search query from components.

        Args:
            keywords: Keywords to search in all fields
            categories: arXiv categories (e.g., cs.CL, cs.CV)
            authors: Author names
            title: Search in title only
            abstract: Search in abstract only
            date_from: Start date filter
            date_to: End date filter

        Returns:
            arXiv query string
        """
        parts = []

        # Keywords (search in all fields)
        if keywords:
            keyword_query = " AND ".join(f'all:"{kw}"' for kw in keywords)
            parts.append(f"({keyword_query})")

        # Categories
        if categories:
            cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
            parts.append(f"({cat_query})")

        # Authors
        if authors:
            author_query = " OR ".join(f'au:"{author}"' for author in authors)
            parts.append(f"({author_query})")

        # Title
        if title:
            parts.append(f'ti:"{title}"')

        # Abstract
        if abstract:
            parts.append(f'abs:"{abstract}"')

        # Date range
        if date_from or date_to:
            from_str = date_from.strftime("%Y%m%d") if date_from else "*"
            to_str = date_to.strftime("%Y%m%d") if date_to else "*"
            parts.append(f"submittedDate:[{from_str} TO {to_str}]")

        return " AND ".join(parts) if parts else "all:*"


# Singleton instance
_arxiv_service: Optional[ArxivService] = None


def get_arxiv_service() -> ArxivService:
    """Get singleton instance of ArxivService."""
    global _arxiv_service
    if _arxiv_service is None:
        _arxiv_service = ArxivService()
    return _arxiv_service


# Common arXiv categories for reference
ARXIV_CATEGORIES = {
    # Computer Science
    "cs.AI": "Artificial Intelligence",
    "cs.CL": "Computation and Language (NLP)",
    "cs.CV": "Computer Vision and Pattern Recognition",
    "cs.LG": "Machine Learning",
    "cs.IR": "Information Retrieval",
    "cs.DB": "Databases",
    "cs.DC": "Distributed, Parallel, and Cluster Computing",
    "cs.DS": "Data Structures and Algorithms",
    "cs.GT": "Game Theory",
    "cs.HC": "Human-Computer Interaction",
    "cs.MA": "Multiagent Systems",
    "cs.MM": "Multimedia",
    "cs.NE": "Neural and Evolutionary Computing",
    "cs.OS": "Operating Systems",
    "cs.PF": "Performance",
    "cs.RO": "Robotics",
    "cs.SC": "Symbolic Computation",
    "cs.SD": "Sound",
    "cs.SE": "Software Engineering",
    "cs.SY": "Systems and Control",

    # Statistics
    "stat.ML": "Machine Learning (Stats)",
    "stat.AP": "Applications",
    "stat.CO": "Computation",
    "stat.ME": "Methodology",
    "stat.TH": "Statistics Theory",

    # Mathematics
    "math.NA": "Numerical Analysis",
    "math.OC": "Optimization and Control",
    "math.PR": "Probability",
    "math.ST": "Statistics (Math)",

    # Physics
    "physics.comp-ph": "Computational Physics",
    "physics.data-an": "Data Analysis, Statistics and Probability",

    # Electrical Engineering
    "eess.AS": "Audio and Speech Processing",
    "eess.IV": "Image and Video Processing",
    "eess.SP": "Signal Processing",
    "eess.SY": "Systems and Control",

    # Quantitative Biology
    "q-bio.BM": "Biomolecules",
    "q-bio.CB": "Cell Behavior",
    "q-bio.GN": "Genomics",
    "q-bio.MN": "Molecular Networks",
    "q-bio.NC": "Neurons and Cognition",
    "q-bio.OT": "Other Quantitative Biology",
    "q-bio.PE": "Populations and Evolution",
    "q-bio.QM": "Quantitative Methods",
    "q-bio.SC": "Subcellular Processes",
    "q-bio.TO": "Tissues and Organs",
}
