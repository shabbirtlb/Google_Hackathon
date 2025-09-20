import re
from typing import Union, Dict, Any, List
from growth_metrics import extract_startup_growth_metrics
def convert_string_to_number(value: Union[str, int, float]) -> float:
    """
    Convert various string formats to numerical values
    Supports: $875M, 50K, 10,000, 1.5B, 25%, etc.
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        return 0.0
    
    # Remove commas, spaces, and dollar signs
    clean_value = value.replace(',', '').replace(' ', '').replace('$', '').strip()
    
    # Handle percentage values
    if '%' in clean_value:
        clean_value = clean_value.replace('%', '')
        try:
            return float(clean_value) / 100  # Convert percentage to decimal
        except ValueError:
            return 0.0
    
    # Handle ranges (e.g., "50-100M")
    if '-' in clean_value and not clean_value.startswith('-'):
        parts = clean_value.split('-')
        try:
            # Take the midpoint of the range
            return (convert_string_to_number(parts[0]) + convert_string_to_number(parts[1])) / 2
        except (ValueError, IndexError):
            return 0.0
    
    # Handle abbreviations (K, M, B, T)
    multiplier = 1
    if clean_value.upper().endswith('K'):
        multiplier = 1_000
        clean_value = clean_value[:-1]
    elif clean_value.upper().endswith('M'):
        multiplier = 1_000_000
        clean_value = clean_value[:-1]
    elif clean_value.upper().endswith('B'):
        multiplier = 1_000_000_000
        clean_value = clean_value[:-1]
    elif clean_value.upper().endswith('T'):
        multiplier = 1_000_000_000_000
        clean_value = clean_value[:-1]
    
    # Convert to float and apply multiplier
    try:
        return float(clean_value) * multiplier
    except ValueError:
        return 0.0

def extract_numeric_value(text: str, pattern: str = None) -> float:
    """
    Extract numeric value from text using regex patterns
    """
    if pattern:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return convert_string_to_number(match.group(1))
    return 0.0

def parse_financial_data(finance_data: Dict[str, Any], finance_summary: Dict[str, Any]) -> Dict[str, float]:
    """
    Parse all financial data into numerical values
    """
    results = {}
    
    # Parse total funding
    results['total_funding'] = convert_string_to_number(
        finance_data.get('total_funding', '$0')
    )
    
    # Parse acquisition price
    acquisition_price = finance_summary.get('acquisition', {}).get('price', '$0')
    results['acquisition_price'] = convert_string_to_number(acquisition_price)
    
    # Parse revenue estimate (handle ranges)
    revenue_estimate = finance_summary.get('latest_revenue_estimate', '$0')
    results['revenue_estimate'] = convert_string_to_number(revenue_estimate)
    
    # Parse employee count with fallbacks
    employees = finance_summary.get("no_of_employees", 
                                  finance_summary.get("employee_count", "50"))
    results['employees'] = convert_string_to_number(employees)
    
    # Parse customer base with fallbacks
    customers = finance_summary.get("customer_base_size", 
                                  finance_summary.get("customers", "10"))
    results['customers'] = convert_string_to_number(customers)
    
    # Parse valuation estimate
    valuation = finance_summary.get('latest_valuation_estimate', '$0')
    results['valuation_estimate'] = convert_string_to_number(valuation)
    
    return results

def parse_funding_rounds(funding_rounds: list) -> list:
    """
    Parse all funding rounds into numerical values
    """
    parsed_rounds = []
    
    for round_data in funding_rounds:
        parsed_round = round_data.copy()
        
        # Convert money raised
        if 'money_raised' in round_data:
            parsed_round['money_raised_numeric'] = convert_string_to_number(
                round_data['money_raised']
            )
        
        parsed_rounds.append(parsed_round)
    
    return parsed_rounds

def calculate_financial_metrics(parsed_data: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate financial metrics from parsed numerical data
    """
    metrics = {}
    # print(parsed_data['revenue_estimate'])
    # Basic metrics
    metrics['revenue_multiple'] = (
        parsed_data['acquisition_price'] / parsed_data['revenue_estimate'] 
        if parsed_data['revenue_estimate'] > 0 else 0
    )
    
    metrics['funding_multiple'] = (
        parsed_data['acquisition_price'] / parsed_data['total_funding'] 
        if parsed_data['total_funding'] > 0 else 0
    )
    
    metrics['value_per_employee'] = (
        parsed_data['acquisition_price'] / parsed_data['employees'] 
        if parsed_data['employees'] > 0 else 0
    )
    
    metrics['value_per_customer'] = (
        parsed_data['acquisition_price'] / parsed_data['customers'] 
        if parsed_data['customers'] > 0 else 0
    )
    
    metrics['funding_efficiency'] = (
        parsed_data['revenue_estimate'] / parsed_data['total_funding'] 
        if parsed_data['total_funding'] > 0 else 0
    )
    metrics['revenue_estimate'] = parsed_data['revenue_estimate']
    metrics['total_funding'] = parsed_data['total_funding']
    return metrics

# Example usage with your data
def process_all_financial_data(finance_data, finance_summary):
    """
    Complete processing of all financial data
    """
    # Parse all string values to numbers
    parsed_data = parse_financial_data(finance_data, finance_summary)
    # print(parsed_data)
    # Parse funding rounds if available
    if 'funding_rounds' in finance_data:
        parsed_funding_rounds = parse_funding_rounds(finance_data['funding_rounds'])
        parsed_data['funding_rounds_numeric'] = parsed_funding_rounds
    
    # Calculate financial metrics
    metrics = calculate_financial_metrics(parsed_data)
    # print(f"metrics:",metrics)
    return metrics


def extract_growth_signals(article_data):
    """Extract growth indicators from article content"""
    growth_signals = []
    
    for article in article_data:
        content = article.get('content', '').lower()
        
        signals = {
            'customer_growth': any(term in content for term in ['growing', 'expanding', 'increasing', 'added']),
            'market_traction': any(term in content for term in ['traction', 'adoption', 'usage', 'demand']),
            'competitive_advantage': any(term in content for term in ['unique', 'advantage', 'different', 'superior']),
            'sector_tailwinds': any(term in content for term in ['digital transformation', 'industry 4.0', 'innovation'])
        }
        
        if any(signals.values()):
            growth_signals.append({
                'article': article['url'],
                'signals': signals,
                'key_quotes': extract_key_quotes(article['content'])
            })
    
    return growth_signals

def extract_key_quotes(content):
    """Extract meaningful quotes that indicate growth or success"""
    sentences = re.split(r'[.!?]+', content)
    key_quotes = []
    
    for sentence in sentences:
        if any(term in sentence.lower() for term in ['growth', 'success', 'leader', 'innovative', 'disrupt']):
            key_quotes.append(sentence.strip())
    
    return key_quotes[:3]  # Return top 3 quotes

def generate_sector_benchmarks(financial_metrics):
    """Generate sector benchmarks based on available data"""
    
    # These would ideally come from industry research, but we can estimate
    # based on the acquisition multiple and known sector data
    
    sector_data = {
        'construction_tech_multiple_range': '8-15x revenue',
        'typical_funding_efficiency': '1.5-3.0x (revenue/total funding)',
        'employee_growth_rate': '20-35% YoY for successful startups',
        'customer_acquisition_cost': '$15,000-50,000 for enterprise SaaS'
    }
    
    # Compare company performance to sector benchmarks
    comparison = {
        'revenue_multiple': {
            'company': financial_metrics['revenue_multiple'],
            'sector_median': 10.0,
            'assessment': 'above_average' if financial_metrics['revenue_multiple'] > 10 else 'average'
        },
        'funding_efficiency': {
            'company': round(financial_metrics['revenue_estimate'] / financial_metrics['total_funding'], 1),
            'sector_median': 2.0,
            'assessment': 'efficient' if (financial_metrics['revenue_estimate'] / financial_metrics['total_funding']) > 2.0 else 'average'
        }
    }
    
    return {
        'sector_benchmarks': sector_data,
        'company_vs_sector': comparison
    }

def perform_complete_analysis(combined_data, crunchbase_data, finance_data, financial_summary,weights):
    """Perform complete analysis using all available data"""
    
    # Extract detailed article data
    growth_metrics = extract_startup_growth_metrics(combined_data)

    
    # # Analyze competitors
    # competitor_analysis = analyze_competitors(
    #     crunchbase_data['financial_estimates_and_competitors']['competitors'],
    #     crunchbase_data['crunchbase_insights']['similar_companies']
    # )
    
    # Calculate financial metrics
    financial_metrics = process_all_financial_data(finance_data, financial_summary)
    
    
    # Generate sector benchmarks
    benchmarks = generate_sector_benchmarks(financial_metrics)
    # print("Benchmarks:\n",benchmarks)
    # print("Financial metrics\n",financial_metrics)
    # print("growth metrics\n",growth_metrics)
    # Compile final report
    final_report = {
        'company_overview': {
            'description': crunchbase_data['basic_company_info']['description'],
            'status': crunchbase_data['basic_company_info']['status'],
            'acquisition': financial_summary['acquisition']
        },
        'financial_analysis': financial_metrics,
        'growth_indicators': growth_metrics,
        'sector_benchmarks': benchmarks,
        'investment_recommendation': generate_recommendation(financial_metrics, benchmarks, growth_metrics,weights)
    }
    
    return final_report

def parse_sector_multiple(multiple_str: str) -> float:
    """
    Parse sector multiple string and extract numeric value
    
    Args:
        multiple_str: String containing multiple (e.g., "15x revenue", "10-15x", "15")
        
    Returns:
        Float value of the multiple, or 0.0 if parsing fails
    """
    if not multiple_str or not isinstance(multiple_str, str):
        return 0.0
    
    try:
        # Remove common suffixes and non-numeric characters
        clean_str = multiple_str.lower()
        clean_str = clean_str.replace('x revenue', '').replace('x', '').replace('revenue', '').strip()
        
        # Handle range format (e.g., "10-15")
        if '-' in clean_str:
            parts = clean_str.split('-')
            if len(parts) == 2:
                # Take the maximum value from the range
                max_value = parts[1].strip()
                return float(max_value)
        
        # Handle single value
        return float(clean_str)
        
    except (ValueError, AttributeError, IndexError) as e:
        print(f"Warning: Could not parse sector multiple '{multiple_str}': {e}")
        return 0.0

# Alternative: if you want to be more defensive about the benchmarks structure
def get_sector_multiple_max(benchmarks: Dict[str, Any], default_range: str = '0-15') -> float:
    """
    Safely extract sector multiple maximum from benchmarks data
    
    Args:
        benchmarks: Dictionary containing benchmark data
        default_range: Default range string to use if extraction fails
        
    Returns:
        Maximum multiple value as float
    """
    try:
        if not benchmarks or not isinstance(benchmarks, dict):
            multiple_str = default_range
        else:
            sector_benchmarks = benchmarks.get('sector_benchmarks', {})
            if not isinstance(sector_benchmarks, dict):
                multiple_str = default_range
            else:
                multiple_str = sector_benchmarks.get('construction_tech_multiple_range', default_range)
        
        return parse_sector_multiple(multiple_str)
        
    except Exception as e:
        print(f"Warning: Error extracting sector multiple: {e}")
        return parse_sector_multiple(default_range)


def generate_recommendation(metrics, benchmarks, growth_signals,weights):
    """
    Generate investor-ready recommendation with customizable weightages.
    """
    total_weight = sum(weights.values())

    positive_factors, risk_factors = [], []

    # --- Financial Subscore (0–100) ---
    financial_subscore = 0
    sector_multiple_max = parse_sector_multiple(
        benchmarks.get('sector_benchmarks', {}).get('construction_tech_multiple_range', '0-15')
    )

    if metrics['revenue_multiple'] <= sector_multiple_max:
        financial_subscore += 60
        positive_factors.append("Revenue multiple within sector range")
    else:
        financial_subscore += 30
        risk_factors.append("High revenue multiple vs sector norm")

    funding_efficiency = metrics.get('funding_efficiency', 0)
    sector_efficiency_median = benchmarks.get('sector_benchmarks', {}).get('funding_efficiency', {}).get('median', 1.8)

    if funding_efficiency >= sector_efficiency_median:
        financial_subscore += 40
        positive_factors.append("Good funding efficiency")
    else:
        financial_subscore += 15
        risk_factors.append("Below-average funding efficiency")

    financial_subscore = min(financial_subscore, 100)

    # --- Growth Subscore (0–100) ---
    growth_subscore = 0
    funding_timeline = growth_signals.get('funding_growth_timeline', [])
    if len(funding_timeline) >= 3:
        growth_subscore += 40
        positive_factors.append("Strong funding trajectory")
    elif len(funding_timeline) == 2:
        growth_subscore += 25
    else:
        growth_subscore += 10

    customer_metrics = growth_signals.get('customer_acquisition_metrics', {})
    if customer_metrics.get('total_customers', 0) > 5000:
        growth_subscore += 25
    if customer_metrics.get('customer_growth_rate', 0) > 30:
        growth_subscore += 20
    team_metrics = growth_signals.get('team_growth_indicators', {})
    if team_metrics.get('employee_count', 0) > 100:
        growth_subscore += 10
    if team_metrics.get('hiring_momentum', False):
        growth_subscore += 5

    growth_subscore = min(growth_subscore, 100)

    # --- Market Subscore (0–100) ---
    market_subscore = 0
    if metrics.get('acquisition_price', 0) > metrics.get('total_funding', 0) * 5:
        market_subscore += 50
    trend_analysis = growth_signals.get('growth_trend_analysis', {})
    if trend_analysis.get('funding_velocity') == 'rapid':
        market_subscore += 25
    if trend_analysis.get('customer_velocity') == 'high_velocity':
        market_subscore += 25

    market_subscore = min(market_subscore, 100)

    # --- Risk Subscore (0–100, higher = riskier) ---
    risk_subscore = 0
    if metrics['revenue_multiple'] > sector_multiple_max * 1.5:
        risk_subscore += 40
        risk_factors.append("Extremely high revenue multiple")
    if funding_efficiency < sector_efficiency_median * 0.5:
        risk_subscore += 40
        risk_factors.append("Very poor funding efficiency")
    if not trend_analysis.get('growth_consistency', False):
        risk_subscore += 20
        risk_factors.append("Inconsistent growth patterns")
    risk_subscore = min(risk_subscore, 100)

    # --- Weighted Final Score ---
    weighted_score = (
        financial_subscore * weights["financial"] +
        growth_subscore * weights["growth"] +
        market_subscore * weights["market"] +
        (100 - risk_subscore) * weights["risk"]   # invert risk: less risk = higher score
    ) / total_weight

    reasoning = generate_detailed_reasoning(weighted_score, positive_factors, risk_factors, growth_signals)

    return {
        "rating": get_rating(weighted_score),
        "score": round(weighted_score),
        "reasoning": reasoning,
        "positive_factors": positive_factors,
        "risk_factors": risk_factors,
        "growth_indicators": extract_key_growth_indicators(growth_signals)
    }


def get_rating(score: float) -> str:
    """Get rating based on score"""
    if score >= 85:
        return "STRONG BUY"
    elif score >= 70:
        return "BUY"
    elif score >= 55:
        return "HOLD"
    elif score >= 40:
        return "WEAK HOLD"
    else:
        return "SELL"

def generate_detailed_reasoning(score: float, positive_factors: List[str], 
                               risk_factors: List[str], growth_signals: Dict[str, Any]) -> str:
    """Generate detailed reasoning for the recommendation"""
    
    reasoning_parts = []
    
    # Introduction
    reasoning_parts.append(f"Investment Recommendation Score: {score}/100")
    
    # Positive factors
    if positive_factors:
        reasoning_parts.append("\nStrengths:")
        for factor in positive_factors:
            reasoning_parts.append(f"• {factor}")
    
    # Risk factors
    if risk_factors:
        reasoning_parts.append("\nRisks:")
        for factor in risk_factors:
            reasoning_parts.append(f"• {factor}")
    
    # Growth highlights
    growth_metrics = growth_signals.get('customer_acquisition_metrics', {})
    if growth_metrics:
        reasoning_parts.append("\nGrowth Highlights:")
        reasoning_parts.append(f"• Customer base: {growth_metrics.get('total_customers', 0):,.0f}")
        reasoning_parts.append(f"• User base: {growth_metrics.get('total_users', 0):,.0f}")
        reasoning_parts.append(f"• Growth rate: {growth_metrics.get('customer_growth_rate', 0):.0f}%")
    
    # Funding timeline
    funding_timeline = growth_signals.get('funding_growth_timeline', [])
    if funding_timeline:
        reasoning_parts.append(f"\nFunding History ({len(funding_timeline)} rounds):")
        for round_data in funding_timeline:
            reasoning_parts.append(f"• {round_data['year']}: {round_data['amount']}")
    
    return "\n".join(reasoning_parts)

def extract_key_growth_indicators(growth_signals: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key growth indicators for quick reference"""
    return {
        'funding_rounds_count': len(growth_signals.get('funding_growth_timeline', [])),
        'total_customers': growth_signals.get('customer_acquisition_metrics', {}).get('total_customers', 0),
        'employee_count': growth_signals.get('team_growth_indicators', {}).get('employee_count', 0),
        'growth_score': growth_signals.get('growth_score', 0),
        'funding_velocity': growth_signals.get('growth_trend_analysis', {}).get('funding_velocity', 'unknown'),
        'company_age': growth_signals.get('growth_trend_analysis', {}).get('acquisition_timeline', {}).get('company_age_at_acquisition', 0)
    }