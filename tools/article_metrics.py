import json
from typing import List, Dict, Any
from collections import defaultdict

def combine_article_extractions(article_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Combine multiple article extraction JSONs into a unified structure
    
    Args:
        article_data_list: List of article extraction JSON objects
        
    Returns:
        Combined JSON with deduplicated and merged data
    """
    
    combined = {
        "sources": [],
        "combined_data": {
            "dollar_amounts": [],
            "customer_metrics": [],
            "employee_counts": [],
            "dates_and_timeline": [],
            "exact_quotes": [],
            "all_numerical_data": {}
        },
        "summary_metrics": {},
        "extraction_metadata": {
            "total_articles": 0,
            "articles_with_tool_used": 0,
            "earliest_extraction": None,
            "latest_extraction": None
        }
    }
    
    # Track unique values to avoid duplicates
    unique_dollar_amounts = set()
    unique_customer_metrics = set()
    unique_employee_counts = set()
    unique_dates = set()
    unique_quotes = set()
    
    for article_data in article_data_list:
        # Add source information
        combined["sources"].append({
            "url": article_data.get("source_url", "unknown"),
            "extraction_timestamp": article_data.get("extraction_timestamp", "unknown")
        })
        
        # Update metadata
        combined["extraction_metadata"]["total_articles"] += 1
        if article_data.get("tool_used", False):
            combined["extraction_metadata"]["articles_with_tool_used"] += 1
        
        # Process extracted data
        extracted_data = article_data.get("extracted_data", {})
        
        # Dollar amounts
        for amount in extracted_data.get("dollar_amounts", []):
            unique_dollar_amounts.add(amount.strip())
        
        # Customer metrics
        for metric in extracted_data.get("customer_metrics", []):
            unique_customer_metrics.add(metric.strip())
        
        # Employee counts
        for count in extracted_data.get("employee_counts", []):
            unique_employee_counts.add(count.strip())
        
        # Dates and timeline
        for date in extracted_data.get("dates_and_timeline", []):
            unique_dates.add(date.strip())
        
        # Exact quotes
        for quote in extracted_data.get("exact_quotes", []):
            unique_quotes.add(quote.strip())
    
    # Convert sets back to sorted lists
    combined["combined_data"]["dollar_amounts"] = sorted(list(unique_dollar_amounts))
    combined["combined_data"]["customer_metrics"] = sorted(list(unique_customer_metrics))
    combined["combined_data"]["employee_counts"] = sorted(list(unique_employee_counts))
    combined["combined_data"]["dates_and_timeline"] = sorted(list(unique_dates))
    combined["combined_data"]["exact_quotes"] = sorted(list(unique_quotes))
    
    # Extract and process numerical data
    combined["combined_data"]["all_numerical_data"] = extract_numerical_values(combined["combined_data"])
    
    # Generate summary metrics
    combined["summary_metrics"] = generate_summary_metrics(combined["combined_data"]["all_numerical_data"])
    
    return combined

def extract_numerical_values(combined_data: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Extract and convert numerical values from combined data
    """
    numerical_data = {
        "funding_amounts": [],
        "acquisition_prices": [],
        "customer_counts": [],
        "employee_counts": [],
        "project_counts": [],
        "dates": [],
        "converted_values": {}
    }
    
    # Helper function to convert string to number (from previous implementation)
    def convert_string_to_number(value):
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str):
            return 0.0
        
        clean_value = value.replace(',', '').replace(' ', '').replace('$', '').strip()
        
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
        
        try:
            return float(clean_value) * multiplier
        except ValueError:
            return 0.0
    
    # Process dollar amounts
    for amount in combined_data["dollar_amounts"]:
        numerical_value = convert_string_to_number(amount)
        if numerical_value > 0:
            if "acquisition" in amount.lower() or "buy" in amount.lower():
                numerical_data["acquisition_prices"].append(numerical_value)
            else:
                numerical_data["funding_amounts"].append(numerical_value)
    
    # Process customer metrics
    for metric in combined_data["customer_metrics"]:
        if "customer" in metric.lower():
            numerical_data["customer_counts"].append(convert_string_to_number(metric))
        elif "user" in metric.lower():
            numerical_data["customer_counts"].append(convert_string_to_number(metric))
        elif "project" in metric.lower():
            numerical_data["project_counts"].append(convert_string_to_number(metric))
    
    # Process employee counts
    for count in combined_data["employee_counts"]:
        numerical_data["employee_counts"].append(convert_string_to_number(count))
    
    # Store converted values for easy access
    numerical_data["converted_values"] = {
        "total_funding": sum(numerical_data["funding_amounts"]),
        "acquisition_price": sum(numerical_data["acquisition_prices"]),
        "total_customers": sum(numerical_data["customer_counts"]),
        "total_employees": sum(numerical_data["employee_counts"]),
        "total_projects": sum(numerical_data["project_counts"])
    }
    
    return numerical_data

def generate_summary_metrics(numerical_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate summary metrics from numerical data
    """
    summary = {
        "financial_summary": {
            "total_funding": numerical_data["converted_values"]["total_funding"],
            "acquisition_price": numerical_data["converted_values"]["acquisition_price"],
            "funding_rounds_count": len(numerical_data["funding_amounts"]),
            "largest_funding_round": max(numerical_data["funding_amounts"]) if numerical_data["funding_amounts"] else 0
        },
        "business_metrics": {
            "customer_count": numerical_data["converted_values"]["total_customers"],
            "employee_count": numerical_data["converted_values"]["total_employees"],
            "project_count": numerical_data["converted_values"]["total_projects"],
            "customers_per_employee": (
                numerical_data["converted_values"]["total_customers"] / numerical_data["converted_values"]["total_employees"]
                if numerical_data["converted_values"]["total_employees"] > 0 else 0
            )
        },
        "valuation_metrics": {
            "revenue_multiple_estimate": (
                numerical_data["converted_values"]["acquisition_price"] / 20000000  # Assuming $20M revenue
                if numerical_data["converted_values"]["acquisition_price"] > 0 else 0
            ),
            "price_to_employee": (
                numerical_data["converted_values"]["acquisition_price"] / numerical_data["converted_values"]["total_employees"]
                if numerical_data["converted_values"]["total_employees"] > 0 else 0
            )
        }
    }
    
    return summary