from flask import Flask, render_template, request, jsonify
import os
import requests
from dotenv import load_dotenv
from tools.serp_enrich import serpapi_enrich_company
from tools.article_metrics import combine_article_extractions
from report_gen import perform_complete_analysis
from tools.preprocess import parse_model_response_to_dict
from tools.Doc_Parse import MultiFormatDocumentParser
from agents import (
    get_link_agent,
    get_crunchbase_agent,
    get_news_agent,
    get_financial_enrichment_agent,
    get_investor_analysis_agent
)
from agno.agent import RunResponse  # type:ignore
import json

# Load variables from .env
load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
agentql_api_key = os.getenv("AGENTQL_API_KEY")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


WEIGHTS_FILE = "weights.json"

def load_weights():
    if not os.path.exists(WEIGHTS_FILE):
        return {"financial": 25, "growth": 40, "market": 20, "risk": 15}
    with open(WEIGHTS_FILE, "r") as f:
        return json.load(f)

def save_weights(weights):
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(weights, f, indent=2)

@app.route("/weights", methods=["GET"])
def get_weights():
    return jsonify(load_weights())

@app.route("/weights", methods=["POST"])
def update_weights():
    data = request.json
    save_weights(data)
    return jsonify({"status": "success", "weights": data})

# Fetch all YC companies
def fetch_yc_companies(endpoint="all"):
    url = f"https://yc-oss.github.io/api/companies/{endpoint}.json"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

# Fetch specific company details by API URL (received from frontend)
def fetch_company_details(api_url):
    try:
        resp = requests.get(api_url)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": "Company details not found"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').lower()
    companies = fetch_yc_companies("all")

    def matches_query(company):
        return (
            query in company['name'].lower()
            or query in company.get('one_liner', '').lower()
            or query in company.get('slug', '').lower()
            or any(query in fn.lower() for fn in company.get('former_names', []))
        )
    
    # Step 1: text search
    filtered_companies = [c for c in companies if matches_query(c)]

    # Step 2: additional filters
    batch = request.args.get('batch', '').lower()
    industry = request.args.get('industry', '').lower()
    region = request.args.get('region', '').lower()
    tag = request.args.get('tag', '').lower()
    min_team_size = int(request.args.get('min_team_size', 0))
    max_team_size = int(request.args.get('max_team_size', 1000000))

    if batch:
        filtered_companies = [
            c for c in filtered_companies 
            if batch in c.get('batch', '').lower()
        ]

    if industry:
        filtered_companies = [
            c for c in filtered_companies 
            if any(industry in i.lower() for i in c.get('industries', []))
        ]

    if region:
        filtered_companies = [
            c for c in filtered_companies 
            if any(region in r.lower() for r in c.get('regions', []))
        ]

    if tag:
        filtered_companies = [
            c for c in filtered_companies 
            if any(tag in t.lower() for t in c.get('tags', []))
        ]

    # Team size slider filter
    filtered_companies = [
        c for c in filtered_companies
        if min_team_size <= c.get('team_size', 0) <= max_team_size
    ]

    return jsonify(filtered_companies)



@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        # Handle form data
        company_url = request.form.get("company_url")
        uploaded_files = request.files.getlist("files")  # multiple file support

        if not company_url:
            return jsonify({"error": "company_url is required"}), 400
        link_agent = get_link_agent()
        YCominator_Data : RunResponse = link_agent.run(f"Extract all available links on this page {company_url}",prevent_hallucination = True)
        cleaned_data = parse_model_response_to_dict(YCominator_Data.content)
        # print(f"Ycombinator data:\n",cleaned_data)
        crunchbase_agent = get_crunchbase_agent()
        CrunchBase_Data: RunResponse = crunchbase_agent.run(f"Analyze and find all u can for this crunchbase site : {cleaned_data['crunchbase'][0]}")
        crunch_data = parse_model_response_to_dict(CrunchBase_Data.content)
        # print("Crunchbase Data:",crunch_data)
        # Handle uploaded files (optional, for now just log filenames)
        file_names = []
        all_results = []

        parser = MultiFormatDocumentParser()

        import traceback

        if uploaded_files:
            print("📄 Processing uploaded documents...")

            for f in uploaded_files:
                try:
                    # Save uploaded file properly
                    file_path = os.path.join(UPLOAD_FOLDER, f.filename)
                    f.save(file_path)   # ✅ This is the correct way in Flask

                    print(f"\n📄 Processing: {file_path}")
                    file_names.append(file_path)

                    print(f"\n📄 Processing: {file_path}")
                    file_names.append(file_path)

                    # Extract text
                    text_content = parser.extract_text_from_file(file_path)
                    if not text_content.strip():
                        print("⚠️ No text extracted from file.")
                        continue

                    print(f"✅ Extracted text (preview): {text_content[:300]}...\n")

                    # Extract financial data
                    doc_finance = parser.extract_financial_data(
                        text_content=text_content,
                        source_name=file_path
                    )
                    print(f"💰 Extracted finance data:\n{doc_finance}")

                    all_results.append(doc_finance)

                except FileNotFoundError:
                    print(f"❌ File not found: {f.filename}")

                except ValueError as ve:
                    print(f"⚠️ Unsupported format for {f.filename}: {ve}")

                except Exception as e:
                    print(f"🔥 Unexpected error while processing {f.filename}: {e}")
                    traceback.print_exc()
        news = []
        # Check if 'news_articles' exists, is a list, and is not empty
        if (isinstance(cleaned_data.get('news_articles'), list) and 
            len(cleaned_data['news_articles']) > 0):
            for art in cleaned_data['news_articles']:
                if art is not None:  # Skip None values
                    news.append(art)

        # Check if 'company_news' exists, is a list, and is not empty
        if (isinstance(crunch_data.get('company_news'), list) and 
            len(crunch_data['company_news']) > 0):
            for art in crunch_data['company_news']:
                if art is not None:  # Skip None values
                    news.append(art)
        # print(news)
        search = ""
        metrics = []
        news_agent = get_news_agent()
        if news:
            for n in news:
                try:
                    # Get news results safely
                    news_results = serpapi_enrich_company(n, api_key=os.getenv("SERP_KEY"), search_engine="google_news")
                    
                    # Check if we have valid news results with at least one item
                    if news_results and 'news' in news_results and len(news_results['news']) > 0:
                        search_link = news_results['news'][0]['link']
                        
                        news_summary: RunResponse = news_agent.run(f"""Extract SPECIFIC numerical metrics, financial data, and business indicators from this article: {search_link}
                        
                        Extract:
                        1. Exact funding amounts ($ amounts)
                        2. Revenue figures or estimates
                        3. Customer/user counts
                        4. Employee numbers
                        5. Acquisition prices
                        6. Growth rates or percentages
                        7. Market size mentions
                        8. Key risk factors mentioned
                        9. Strategic quotes with numbers
                        
                        Return ONLY raw data in JSON format, no commentary.""")
                        
                        s = parse_model_response_to_dict(news_summary.content)
                        metrics.append(s)
                        search += f"\n{news_summary.content}"
                    else:
                        print(f"No news results found for: {n}")
                except Exception as e:
                    print(f"Error processing news article {n}: {str(e)}")
                    continue
        print(f"Metrics:\n{metrics}")
        combined_metrics = combine_article_extractions(metrics)
        fin_text = json.dumps(crunch_data['funding_and_investment'], indent=2)
        comp_details = json.dumps(crunch_data['basic_company_info'], indent=2)
        print("Finance Data\n:",fin_text)
        print(f"Company details\n:{comp_details}")
        financial_enrichment = get_financial_enrichment_agent()
        finance_summary : RunResponse = financial_enrichment.run(f"Company INFO: {comp_details} \n Finance Data : {fin_text} \n Company News:{search}")
        fin_sum = parse_model_response_to_dict(finance_summary.content)
        print("financial summary \n",fin_sum)
        # --------------------------------------------------
        report = perform_complete_analysis(combined_metrics,crunchbase_data=crunch_data,finance_data=crunch_data['funding_and_investment'],financial_summary=fin_sum,weights=load_weights())
        print(report)
        investor_analysis = get_investor_analysis_agent()
        agent_input = {
            "document_extracted": all_results,
            "structured_finance": fin_text,
            "structured_company": comp_details
        }

        # Convert dict → JSON string
        agent_prompt = json.dumps(agent_input, indent=2)

        # Send as proper user role message
        comparative_analysis: RunResponse = investor_analysis.run(
            [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"Analyze the following data and highlight inconsistencies, risks, and investor pros/cons:\n\n{agent_prompt}"}
                    ]
                }
            ]
        )
        print(f"Comparitive analysis:{parse_model_response_to_dict(comparative_analysis.content)}")
        comp_result = parse_model_response_to_dict(comparative_analysis.content)
        combined_report = {
        "financial_report": report,
        "comparative_analysis": comp_result
    }
        # Return the single combined object to the frontend
        return jsonify(combined_report), 200


    except Exception as e:
        return jsonify({"error": str(e)}), 500

# New route to get company-specific data from URL passed by frontend
@app.route('/company', methods=['GET'])
def company_details():
    company_api_url = request.args.get('api_url')
    if company_api_url:
        company_data = fetch_company_details(company_api_url)
        return jsonify(company_data)
    return jsonify({"error": "No API URL provided"})

if __name__ == '__main__':
    app.run(debug=True,port=3002,host='0.0.0.0')