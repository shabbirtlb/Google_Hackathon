# YC Company Explorer & AI Investment Analyst

An agentic AI tool that searches Y Combinator's company directory, then runs a multi-agent research pipeline to produce structured, investor-style due-diligence reports on any startup — pulling from Crunchbase, news articles, SerpAPI search results, and user-uploaded documents (PDF/DOCX/PPTX).

Built during the **Google GenAI Hackathon**.


## What it does

1. **Search** — Browse and filter the full YC company directory (batch, industry, region, tags, team size) via the [YC OSS API](https://yc-oss.github.io/api/).
2. **Multi-agent research** — For a selected company, a chain of [Agno](https://github.com/agno-agi/agno) agents (running on Gemini 2.0 Flash) work together to:
   - Extract and categorize all links from the company's page (socials, Crunchbase, LinkedIn, GitHub, news)
   - Scrape and structure Crunchbase data (funding rounds, investors, valuation, acquisitions, competitors)
   - Pull hard financial figures from news coverage using [AgentQL](https://www.agentql.com/)
   - Enrich results with SerpAPI search summaries
3. **Document ingestion** — Upload pitch decks or reports (PDF, DOCX, PPTX, TXT, MD) and extract financial data (funding, revenue, valuation, customer/employee counts) using a Gemini-powered extraction agent. Includes a sample pitch deck (`uploads/PlanGrid_Professional_Pitch.pdf`) for testing.
4. **Growth metrics** — Parse extracted article data into a funding timeline, customer-acquisition signals, and a computed growth score.
5. **Investor memo** — A final agent cross-checks scraped data against uploaded documents, flags inconsistencies and red flags, surfaces positives, and outputs a structured investment recommendation as JSON.
6. **Configurable scoring** — Adjust the weighting (financial / growth / market / risk) used in the final report through a React-based settings modal, persisted to `weights.json`.

## Tech stack

- **Backend:** Python, Flask
- **Agent orchestration:** Agno (multi-agent), Gemini 2.0 Flash
- **Data sources:** YC OSS API, Crunchbase (scraped), SerpAPI, AgentQL
- **Document parsing:** PyPDF2, python-docx, python-pptx
- **Scraping:** BeautifulSoup, Scrapy, Playwright, newspaper3k
- **Frontend:** React (`static/app.js`, `AnalysisPage.js`, `SavedAnalysisPage.js`), served via Flask templates

## Setup

```bash
pip install -r req.txt
```

Create a `.env` file with:

```
GOOGLE_API_KEY=your_gemini_api_key
AGENTQL_API_KEY=your_agentql_api_key
SERPAPI_KEY=your_serpapi_key
```

Run the app:

```bash
python app.py
```

## Project structure

```
app.py                     # Flask app, routes, YC search/filter, weights config
agents.py                  # Agno agent definitions (link, Crunchbase, news, investor analysis)
report_gen.py               # Final report/number-normalization logic
growth_metrics.py            # Derives growth timeline & score from combined data
tools/
  tool.py                    # Link extraction helper
  serp_enrich.py              # SerpAPI enrichment + URL classification
  Doc_Parse.py                 # Multi-format document parser (PDF/DOCX/PPTX)
  preprocess.py                 # Response cleanup/parsing utilities
  article_metrics.py             # Combines multi-source article extractions
static/                            # React frontend (app.js, AnalysisPage.js, SavedAnalysisPage.js, styles.css)
templates/index.html                # Flask-served entry point
uploads/                              # Sample document(s) for testing document ingestion
```

## Status

Hackathon build — functional end-to-end but not hardened for production use (no auth, limited error handling, API keys required for full functionality).
