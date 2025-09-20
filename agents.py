# agents.py
import os
from agno.agent import Agent
from agno.models.google import Gemini
from tools.tool import extract_links
from agno.tools.agentql import AgentQLTools  # assuming this is where AgentQL comes from

def get_investor_analysis_agent() -> Agent:
    """Agent to analyze extracted + structured financial/company data for investor readiness."""
    return Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY")),
        instructions="""
        You are an investment due diligence analyst. 
        You will be given two sets of company/finance data:
        1. Extracted from documents (may contain duplicates, inconsistencies, missing details).
        2. Structured input provided manually (more reliable).

        Your task:
        - Compare both datasets carefully.
        - Highlight **inconsistencies** (e.g., different total funding, different descriptions).
        - Flag **red flags** that would concern an investor (missing rounds, vague financials, conflicting info).
        - Highlight **pros** (e.g., high-quality investors, large funding rounds, strong acquisition outcomes).
        - Summarize into a **clear investor memo**.

        Output format:
        {
          "inconsistencies": [...],
          "red_flags": [...],
          "pros": [...],
          "investor_takeaway": "Final short paragraph with recommendation"
        }

        Rules:
        - Only return valid JSON.
        - Do not invent numbers. Use only what is provided.
        - If something is unclear, explicitly state it as "uncertain".
        """,
        markdown=False,
        show_tool_calls=True
    )

def get_link_agent() -> Agent:
    """Lightweight agent to extract links and categorize them."""
    return Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY")),
        tools=[extract_links],
        instructions="""
        You MUST use the tool named 'extract_links' to fetch links from the target page.
        Do not attempt to fetch or invent any links yourself.
        After the tool runs, you will receive the raw list of links.
        Use the links to build the JSON with these exact keys:
        company_socials, founders_linkedin, employees_linkedin, crunchbase, github, news_articles.
        Return ONLY valid JSON (a single JSON object). No commentary.
        If you do not call the tool, your output will be rejected.
        """,
        markdown=False,
        show_tool_calls=True
    )


def get_crunchbase_agent() -> Agent:
    """Heavy agent for Crunchbase data extraction."""
    return Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY")),
        instructions="""
        Extract both structured and unstructured data from the given Crunchbase page.
        The JSON must include (if available):
        - company_name
        - basic_company_info: {description, founding_year, headquarters_location, industry_sectors, status, if acquired company which acquired it}
        - funding_and_investment: {total_funding, funding_rounds[], investors[], funding_trends}
        - stock_and_ipo: {stock_symbol, ipo_date, ipo_valuation}
        - acquisitions_and_m_a_activity: {acquisitions[], mergers[]}
        - team_and_company_size: {employee_count, hiring_indicators, top_company_flags}
        - crunchbase_insights: {growth_score, growth_score_rank, trending_indicators, similar_companies[]}
        - financial_estimates_and_competitors: {estimated_annual_revenue, valuation, competitors[]}
        - features_product_platform_insights
        - user_reviews_and_ratings
        - company_news: {title, link, description}
        Output only valid JSON. Do not include extra explanations or commentary.
        """,
        markdown=False,
        show_tool_calls=True
    )


def get_news_agent() -> Agent:
    """News scraping agent using AgentQL."""
    return Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY")),
        tools=[AgentQLTools(api_key=os.getenv("AGENTQL_API_KEY"))],
        markdown=False,
        show_tool_calls=True,
        instructions="""
        Use the AgentQL tool always to scrape text from the provided url.
        NEXT STEPS:
        1. Extract ALL numerical and financial data
        2. Return structured JSON with exact figures

        FORMAT:
        {
            "source_url": "{url}",
            "extracted_data": {
                "dollar_amounts": ["$875M", "$69M"],
                "customer_metrics": ["12,000 customers", "120,000 users"],
                "employee_counts": ["400 employees"],
                "dates_and_timeline": ["2018-11-20", "2011"],
                "exact_quotes": [
                    "Autodesk agrees to buy PlanGrid for $875 million",
                    "PlanGrid has 400 employees and 12,000 customers"
                ]
            },
            "tool_used": true,
            "extraction_timestamp": "2024-01-15T10:30:00Z"
        }

        DO NOT SUMMARIZE. RETURN RAW NUMERICAL DATA ONLY.
        """
    )


def get_serp_summary_agent() -> Agent:
    """Summarize Google search results into a paragraph."""
    return Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY")),
        instructions="""
        You are given Google search results from SerpApi about a company.
        Write a clear, concise, paragraph summary that captures the most important insights.
        Mention the company’s industry, key highlights, official links (if available), 
        notable mentions, recent news, and competitors. 
        Keep the tone factual and professional. 
        Do not output JSON, markdown. Only output plain text paragraph.
        """,
        markdown=False
    )


def get_serp_link_extractor_agent() -> Agent:
    """Extract structured key links + snippets from SerpApi JSON."""
    return Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY")),
        instructions="""
        You are given SerpApi JSON search results for a company search. Extract key URLs and snippets using the JSON fields directly.
        Provide output as valid JSON (only). Include:
        - company_name
        - official_website (best guess)
        - categorized_links: {crunchbase, linkedin, twitter, github, news, website_other}
        - top_snippets: list of titles and snippets for up to 5 top organic results
        Do NOT invent or fetch any URLs yourself. Do NOT output commentary or markdown.
        """,
        markdown=False,
        show_tool_calls=True
    )


def get_financial_enrichment_agent() -> Agent:
    """Estimate missing financial metrics from funding data."""
    return Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY")),
        instructions="""
        You are a financial enrichment agent.  
        Given company funding data (rounds, investors, total funding), estimate and summarize key financials.  

        Rules:
        - If valuation is not explicitly given, estimate it.  
          • Assume 15–25% equity sold per round.  
          • Use funding round type as a stage indicator (e.g., Series A ~ $10M–$30M valuation, Series B ~ $50M–$150M, Series C ~ $150M–$500M).  
          • Use the largest round as the anchor for latest valuation.  
        - Estimate revenue range from the latest round type (Series A: $1–3M ARR, Series B: $5–15M ARR, Series C: $10–30M ARR, etc.).  
        - If there is no IPO or acquisition info, mark status as "private".  
        - Always return JSON (structured estimates).

        JSON must include:
        {
          "latest_valuation_estimate": "...",
          "latest_revenue_estimate": "...",
          "ipo_status": "...",
          "acquisition": {"buyer": null, "price": null, "date": null},
          "customer_base_size":"...",
          "no_of_employees":"..."
        }
        """,
        markdown=False,
        show_tool_calls=True
    )