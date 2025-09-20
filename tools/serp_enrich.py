# serp_enrich.py
import os
import re
import logging
from urllib.parse import urlparse
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
logging.basicConfig(level=logging.INFO)

# --- Helpers ---
def _is_domain(url: str, domain: str) -> bool:
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        return domain.lower() in host
    except:
        return False

def _normalize_url(u: str) -> str:
    # simple normalization
    if not u:
        return u
    if u.startswith("//"):
        u = "https:" + u
    return u.split("?")[0].rstrip("/")

def _classify_url(url: str) -> str:
    """Return a category for a given URL (crunchbase, linkedin, twitter, github, website, news, other)."""
    if not url:
        return "other"
    url = url.lower()
    if "crunchbase.com" in url:
        return "crunchbase"
    if "linkedin.com/in" in url or "linkedin.com/pub" in url or "linkedin.com/company" in url:
        return "linkedin"
    if "twitter.com" in url or "x.com" in url:
        return "twitter"
    if "github.com" in url:
        return "github"
    if re.search(r"/news/|/article|/press|/press-release|/blog", url):
        return "news"
    # trusted site heuristics:
    parsed = urlparse(url)
    host = parsed.netloc if parsed.netloc else url
    # fallback: treat root domain as company website candidate
    return "website" if re.match(r"^[a-z0-9\-\.]+\.[a-z]{2,}$", host) else "other"

def _extract_from_organic(organic: List[dict]) -> List[str]:
    links = []
    for o in organic:
        link = o.get("link") or o.get("url")
        if link:
            links.append(_normalize_url(link))
    return links

# --- Core function ---
def serpapi_enrich_company(company_name: str,
                           api_key: Optional[str] = None,
                           location: Optional[str] = None,
                           search_engine: str = "google",
                           gl: str = "us",
                           hl: str = "en",
                           num: int = 10,
                           device: str = "desktop",
                           no_cache: bool = False) -> Dict:
    """
    Query SerpApi for the company_name and extract categorized links and snippets.

    Returns a dictionary:
    {
      "query_used": "...",
      "top_links": [...],
      "website": "https://...",
      "crunchbase": [...],
      "linkedin": [...],
      "twitter": [...],
      "github": [...],
      "news": [...],
      "knowledge_graph": {...},   # if available
      "organic_snippets": [{title, snippet, link},...],
      "raw_serpapi": {...}  # optional - only included if debug True
    }
    """
    key = api_key or SERPAPI_KEY
    if not key:
        raise RuntimeError("SERPAPI_KEY is not configured in environment")

    q = company_name.strip()
    params = {
        "engine": search_engine,
        "q": q,
        "google_domain": "google.com",
        "gl": gl,
        "hl": hl,
        "device": device,
        "num": num,
        "api_key": key,
        "no_cache": str(int(no_cache))
    }
    if location:
        params["location"] = location

    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=12)
    resp.raise_for_status()
    j = resp.json()

    # Parse organic results
    organic = j.get("organic_results") or j.get("organic") or []
    top_links = _extract_from_organic(organic)

    # include knowledge graph if present
    kg = j.get("knowledge_graph") or j.get("knowledgeGraph")
    kg_site = None
    if kg:
        kg_site = kg.get("website") or kg.get("url")

    # news results
    news_results = j.get("news_results") or j.get("news") or []
    news_links = []
    for n in news_results:
        nl = n.get("link") or n.get("url")
        if nl:
            news_links.append({"title": n.get("title"), "link": _normalize_url(nl), "snippet": n.get("snippet")})

    # related questions
    related_questions = []
    for rq in j.get("related_questions", []) or j.get("people_also_ask", []):
        related_questions.append({"question": rq.get("question"), "answer": rq.get("answer")})

    # Gather all candidate links (organic + top_ads + knowledge + inline)
    candidates = set(top_links)
    # local results if present
    for loc in (j.get("local_results") or j.get("local_results", [])):
        if isinstance(loc, dict):
            for item in loc.get("places", []) or []:
                if item.get("link"):
                    candidates.add(_normalize_url(item["link"]))
    # plus top_ads, inline_links etc.
    for k in ("top_ads", "inline_links", "related_searches", "people_also_ask", "images_results"):
        section = j.get(k) or []
        if isinstance(section, list):
            for it in section:
                link = it.get("link") or it.get("url")
                if link:
                    candidates.add(_normalize_url(link))

    # classify candidates
    classified = {"crunchbase": [], "linkedin": [], "twitter": [], "github": [], "website": [], "news": [], "other": []}
    for url in candidates:
        cat = _classify_url(url)
        if cat in classified:
            if url not in classified[cat]:
                classified[cat].append(url)
        else:
            classified["other"].append(url)

    # also scan organic snippets for titles/snippets
    organic_snippets = []
    for o in organic:
        organic_snippets.append({
            "title": o.get("title"),
            "snippet": o.get("snippet") or o.get("snippet_highlighted"),
            "link": _normalize_url(o.get("link") or o.get("url"))
        })

    # heuristics: prefer kg_site or first website candidate as canonical website
    website = kg_site or (classified["website"][0] if len(classified["website"]) else None)
    # if no direct site, look for a domain among organic top links
    if not website and top_links:
        website = top_links[0]

    result = {
        "query_used": q,
        "top_links": top_links,
        "website": website,
        "classified_links": classified,
        "knowledge_graph": kg or {},
        "organic_snippets": organic_snippets,
        "news": news_links,
        "related_questions": related_questions,
        "serpapi_metadata": {
            "search_id": j.get("search_metadata", {}).get("id"),
            "status": j.get("search_metadata", {}).get("status")
        }
    }
    return result