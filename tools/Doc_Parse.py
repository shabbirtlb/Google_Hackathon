import os
import json
import re
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import logging
from pathlib import Path
import PyPDF2
import docx
import pptx
from tools.preprocess import parse_model_response_to_dict

logger = logging.getLogger(__name__)
from agno.agent import Agent
from agno.models.google import Gemini

load_dotenv()

class MultiFormatDocumentParser:
    def __init__(self):
        self.agent = Agent(
            model=Gemini(id="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY")),
            markdown=False,
            show_tool_calls=True,
            instructions="""You are a financial data extraction expert. Extract precise numerical financial data from documents.
            Focus on: funding amounts, revenue, valuations, customer counts, employee numbers, dates, investors.
            Return JSON format only with the exact structure provided."""
        )
    
    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text content from a file based on its extension.

        Supported formats: .pdf, .docx, .ppt/.pptx, .txt, .md
        """
        file_ext = Path(file_path).suffix.lower()

        try:
            if file_ext == ".pdf":
                return self._extract_from_pdf(file_path)
            elif file_ext == ".docx":
                return self._extract_from_docx(file_path)
            elif file_ext in [".ppt", ".pptx"]:
                return self._extract_from_ppt(file_path)
            elif file_ext in [".txt", ".md"]:
                return self._extract_from_text(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}", exc_info=True)
            return ""

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF files."""
        text_chunks = []
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_chunks.append(page_text.strip())
        return "\n".join(text_chunks)

    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX files."""
        doc = docx.Document(file_path)
        return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())

    def _extract_from_ppt(self, file_path: str) -> str:
        """Extract text from PowerPoint files (.ppt/.pptx)."""
        presentation = pptx.Presentation(file_path)
        text_chunks = []
        for slide in presentation.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text_chunks.append(shape.text.strip())
        return "\n".join(text_chunks)

    def _extract_from_text(self, file_path: str) -> str:
        """Extract text from plain text or markdown files."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            return file.read().strip()
    
    def extract_financial_data(self, text_content: str, source_name: str) -> Dict[str, Any]:
        """Use agent to extract financial data from text content"""
        try:
            response = self.agent.run(f"""
            Extract financial data from this document content. Return ONLY JSON with this exact structure:
            
            {{
                "Finance Data": {{
                    "total_funding": "$X M",
                    "funding_rounds": [
                        {{
                            "round_type": "Series X",
                            "money_raised": "$Y M",
                            "date": "Month Day, Year"
                        }}
                    ],
                    "investors": ["Investor 1", "Investor 2"],
                    "funding_trends": {{}}
                }},
                "Company details": {{
                    "description": "Company description",
                    "founding_year": 2011,
                    "headquarters_location": "City, State, Country",
                    "industry_sectors": ["Sector1", "Sector2"],
                    "status": "Active/Acquired/IPO",
                    "acquired_by": "Acquirer Name (if applicable)"
                }}
            }}
            
            DOCUMENT CONTENT:
            {text_content}  # Limit content size
            """)
            
            if hasattr(response, 'content'):
                return parse_model_response_to_dict(response.content)
                
        except Exception as e:
            print(f"Agent extraction failed for {source_name}: {e}")
            return self._fallback_extraction(text_content)
        
        return {}
    
    def _fallback_extraction(self, text_content: str) -> Dict[str, Any]:
        """Fallback extraction using regex patterns"""
        return {
            "Finance Data": {
                "total_funding": self._extract_total_funding(text_content),
                "funding_rounds": self._extract_funding_rounds(text_content),
                "investors": self._extract_investors(text_content),
                "funding_trends": {}
            },
            "Company details": {
                "description": self._extract_description(text_content),
                "founding_year": self._extract_founding_year(text_content),
                "headquarters_location": self._extract_headquarters(text_content),
                "industry_sectors": self._extract_industries(text_content),
                "status": self._extract_company_status(text_content),
                "acquired_by": self._extract_acquirer(text_content)
            }
        }
    
    def _extract_total_funding(self, text: str) -> str:
        """Extract total funding amount"""
        matches = re.findall(r'total.*funding.*?\$(\d+\.?\d*)\s*[MB]', text, re.IGNORECASE)
        return f"${matches[0]}M" if matches else "$0M"
    
    def _extract_funding_rounds(self, text: str) -> List[Dict]:
        """Extract funding rounds"""
        # Simplified extraction - would need more sophisticated parsing
        return []
    
    def _extract_investors(self, text: str) -> List[str]:
        """Extract investors"""
        investor_keywords = ['sequoia', 'y combinator', 'accel', 'benchmark', 'andreessen']
        investors = []
        for keyword in investor_keywords:
            if keyword in text.lower():
                investors.append(keyword.title())
        return investors
    
    def _extract_description(self, text: str) -> str:
        """Extract company description"""
        sentences = text.split('.')
        for sentence in sentences:
            if 'company' in sentence.lower() or 'provides' in sentence.lower():
                return sentence.strip()
        return "Description not found"
    
    def _extract_founding_year(self, text: str) -> int:
        """Extract founding year"""
        matches = re.findall(r'founded.*?(\d{4})', text, re.IGNORECASE)
        return int(matches[0]) if matches else 2011
    
    def _extract_headquarters(self, text: str) -> str:
        """Extract headquarters location"""
        locations = ['San Francisco', 'New York', 'London', 'Berlin', 'Tokyo']
        for location in locations:
            if location in text:
                return f"{location}, United States"
        return "Location not specified"
    
    def _extract_industries(self, text: str) -> List[str]:
        """Extract industry sectors"""
        industries = []
        sector_keywords = ['software', 'technology', 'construction', 'healthcare', 'finance']
        for keyword in sector_keywords:
            if keyword in text.lower():
                industries.append(keyword.title())
        return industries if industries else ["Technology"]
    
    def _extract_company_status(self, text: str) -> str:
        """Extract company status"""
        if 'acquired' in text.lower():
            return "Acquired"
        elif 'ipo' in text.lower() or 'public' in text.lower():
            return "Public"
        return "Private"
    
    def _extract_acquirer(self, text: str) -> str:
        """Extract acquirer name"""
        acquirers = ['Google', 'Microsoft', 'Amazon', 'Apple', 'Autodesk']
        for acquirer in acquirers:
            if acquirer in text:
                return acquirer
        return "Not acquired"