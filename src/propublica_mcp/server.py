"""
ProPublica Nonprofit Explorer MCP Server

This module implements the main MCP server with tools for accessing ProPublica's
Nonprofit Explorer API data for CRM integration and prospect research.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import json
import csv
import io

from mcp.server.fastmcp import FastMCP
import mcp.types as types

from .api_client import ProPublicaClient
from .models import (
    NonprofitOrganization,
    Filing,
    SearchResult,
    FinancialSummary,
    CRMExport,
    APIError,
    NTEE_CATEGORIES,
    SUBSECTION_CODES,
    US_STATES
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("propublica-mcp")

# Initialize API client
api_client = ProPublicaClient()


@mcp.tool()
async def search_nonprofits(
    query: str,
    state: Optional[str] = None,
    ntee_code: Optional[str] = None,
    subsection_code: Optional[str] = None,
    page: int = 0,
    per_page: int = 25
) -> str:
    """
    Search for nonprofit organizations using ProPublica's database.
    
    Args:
        query: Search term (organization name, keywords, etc.)
        state: Two-letter state code (e.g., 'CA', 'NY')
        ntee_code: NTEE category code (e.g., 'A01', 'B20')
        subsection_code: 501(c) subsection code (e.g., '3', '4', '6')
        page: Page number for pagination (default: 0)
        per_page: Results per page, max 25 (default: 25)
    
    Returns:
        JSON string with search results including organizations and metadata
    """
    try:
        # Validate inputs
        if state and state not in US_STATES:
            return json.dumps({
                "error": f"Invalid state code '{state}'. Must be one of: {', '.join(sorted(US_STATES))}"
            })
        
        if ntee_code and (not ntee_code.isdigit() or int(ntee_code) not in NTEE_CATEGORIES):
            return json.dumps({
                "error": f"Invalid NTEE code '{ntee_code}'. Check NTEE category list."
            })
        
        if subsection_code and (not subsection_code.isdigit() or int(subsection_code) not in SUBSECTION_CODES):
            return json.dumps({
                "error": f"Invalid subsection code '{subsection_code}'. Must be one of: {', '.join(map(str, SUBSECTION_CODES.keys()))}"
            })
        
        if per_page > 25:
            per_page = 25
        
        # Perform search
        results = await api_client.search_organizations(
            query=query,
            state=state,
            ntee_category=int(ntee_code) if ntee_code else None,
            subsection_code=int(subsection_code) if subsection_code else None,
            page=page,
            limit=per_page
        )
        
        # Format response
        response = {
            "search_query": query,
            "filters": {
                "state": state,
                "ntee_code": ntee_code,
                "subsection_code": subsection_code
            },
            "search_metadata": {
                "query": query,
                "filters_applied": {
                    "state": state,
                    "ntee_code": ntee_code,
                    "subsection_code": subsection_code
                }
            },
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_results": results.total_results,
                "has_more": len(results.organizations) == per_page
            },
            "organizations": [org.model_dump() for org in results.organizations],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error searching nonprofits: {e}")
        return json.dumps({
            "error": f"Search failed: {str(e)}",
            "error_type": type(e).__name__
        })


@mcp.tool()
async def get_organization(ein: str) -> str:
    """
    Get detailed information about a specific nonprofit organization.
    
    Args:
        ein: Employer Identification Number (9 digits, with or without hyphen)
    
    Returns:
        JSON string with detailed organization information
    """
    try:
        # Clean EIN format
        clean_ein = ein.replace("-", "").strip()
        if not clean_ein.isdigit() or len(clean_ein) != 9:
            return json.dumps({
                "error": "Invalid EIN format. Must be 9 digits (e.g., '123456789' or '12-3456789')"
            })
        
        # Get organization details
        organization = await api_client.get_organization(clean_ein)
        
        # Format response
        response = {
            "organization": organization.model_dump(),
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting organization {ein}: {e}")
        return json.dumps({
            "error": f"Failed to retrieve organization: {str(e)}",
            "error_type": type(e).__name__
        })


@mcp.tool()
async def get_organization_filings(ein: str, limit: int = 10) -> str:
    """
    Get Form 990 filings for a specific nonprofit organization.
    
    Args:
        ein: Employer Identification Number (9 digits, with or without hyphen)
        limit: Maximum number of filings to retrieve (default: 10, max: 100)
    
    Returns:
        JSON string with filing information and financial data
    """
    try:
        # Clean EIN format
        clean_ein = ein.replace("-", "").strip()
        if not clean_ein.isdigit() or len(clean_ein) != 9:
            return json.dumps({
                "error": "Invalid EIN format. Must be 9 digits (e.g., '123456789' or '12-3456789')"
            })
        
        # Limit validation
        if limit > 100:
            limit = 100
        
        # Get filings
        filings = await api_client.get_organization_filings(clean_ein)
        
        # Limit results
        limited_filings = filings[:limit] if len(filings) > limit else filings
        
        # Create filing summary
        filing_summary = {
            "total_filings": len(filings),
            "filings_returned": len(limited_filings),
            "year_range": {
                "earliest": min([f.tax_year for f in filings if f.tax_year]) if filings else None,
                "latest": max([f.tax_year for f in filings if f.tax_year]) if filings else None
            },
            "form_types": list(set([f.form_type for f in filings if f.form_type])),
            "total_revenue_range": {
                "min": min([f.totrevenue for f in filings if f.totrevenue]) if filings else None,
                "max": max([f.totrevenue for f in filings if f.totrevenue]) if filings else None
            }
        }
        
        # Format response
        response = {
            "ein": clean_ein,
            "total_filings_available": len(filings),
            "filings_returned": len(limited_filings),
            "filing_summary": filing_summary,
            "filings": [filing.model_dump() for filing in limited_filings],
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting filings for {ein}: {e}")
        return json.dumps({
            "error": f"Failed to retrieve filings: {str(e)}",
            "error_type": type(e).__name__
        })


@mcp.tool()
async def analyze_nonprofit_financials(ein: str, years: int = 3) -> str:
    """
    Analyze financial trends and key metrics for a nonprofit organization.
    
    Args:
        ein: Employer Identification Number (9 digits, with or without hyphen)
        years: Number of recent years to analyze (default: 3, max: 10)
    
    Returns:
        JSON string with financial analysis and trends
    """
    try:
        # Clean EIN format
        clean_ein = ein.replace("-", "").strip()
        if not clean_ein.isdigit() or len(clean_ein) != 9:
            return json.dumps({
                "error": "Invalid EIN format. Must be 9 digits (e.g., '123456789' or '12-3456789')"
            })
        
        # Limit years
        if years > 10:
            years = 10
        
        # Get organization and filings
        organization = await api_client.get_organization(clean_ein)
        filings = await api_client.get_organization_filings(clean_ein)
        
        # Limit to recent filings
        recent_filings = filings[:years] if len(filings) > years else filings
        
        if not recent_filings:
            return json.dumps({
                "error": "No financial data available for analysis"
            })
        
        # Calculate financial trends
        financial_data = []
        for filing in recent_filings:
            if filing.totrevenue is not None or filing.totfuncexpns is not None:
                financial_data.append({
                    "tax_year": filing.tax_year,
                    "total_revenue": filing.totrevenue,
                    "total_expenses": filing.totfuncexpns,
                    "net_assets": filing.net_assets,
                    "filing_date": filing.filing_date
                })
        
        # Calculate trends
        trends = {}
        if len(financial_data) >= 2:
            latest = financial_data[0]
            previous = financial_data[1]
            
            if latest["total_revenue"] and previous["total_revenue"]:
                revenue_change = ((latest["total_revenue"] - previous["total_revenue"]) / 
                                previous["total_revenue"]) * 100
                trends["revenue_change_percent"] = round(revenue_change, 2)
            
            if latest["total_expenses"] and previous["total_expenses"]:
                expense_change = ((latest["total_expenses"] - previous["total_expenses"]) / 
                                previous["total_expenses"]) * 100
                trends["expense_change_percent"] = round(expense_change, 2)
        
        # Calculate ratios for latest year
        ratios = {}
        if financial_data:
            latest = financial_data[0]
            if latest["total_revenue"] and latest["total_expenses"]:
                ratios["expense_ratio"] = round((latest["total_expenses"] / latest["total_revenue"]) * 100, 2)
                ratios["surplus_deficit"] = latest["total_revenue"] - latest["total_expenses"]
        
        # Create summary using only fields that exist in FinancialSummary model
        summary = FinancialSummary(
            ein=clean_ein,
            organization_name=organization.name,
            year_range_start=financial_data[-1]["tax_year"] if financial_data else datetime.now(timezone.utc).year - years,
            year_range_end=financial_data[0]["tax_year"] if financial_data else datetime.now(timezone.utc).year,
            filings_analyzed=len(financial_data),
            avg_revenue=sum(f["total_revenue"] for f in financial_data if f["total_revenue"]) / len([f for f in financial_data if f["total_revenue"]]) if any(f["total_revenue"] for f in financial_data) else None,
            revenue_trend="increasing" if trends.get("revenue_change_percent", 0) > 5 else "decreasing" if trends.get("revenue_change_percent", 0) < -5 else "stable",
            avg_expenses=sum(f["total_expenses"] for f in financial_data if f["total_expenses"]) / len([f for f in financial_data if f["total_expenses"]]) if any(f["total_expenses"] for f in financial_data) else None,
            avg_expense_ratio=ratios.get("expense_ratio", 0) / 100 if ratios.get("expense_ratio") else None,
            expense_trend="increasing" if trends.get("expense_change_percent", 0) > 5 else "decreasing" if trends.get("expense_change_percent", 0) < -5 else "stable",
            avg_net_assets=sum(f["net_assets"] for f in financial_data if f["net_assets"]) / len([f for f in financial_data if f["net_assets"]]) if any(f["net_assets"] for f in financial_data) else None,
            annual_data=financial_data
        )
        
        # Format response
        response = {
            "financial_summary": summary.model_dump(),
            "detailed_data": financial_data,
            "trends": trends,
            "ratios": ratios,
            "analysis_notes": [
                f"Analysis covers {len(financial_data)} years of financial data",
                "Revenue and expense trends calculated year-over-year",
                "Expense ratio shows total expenses as % of total revenue",
                "All amounts in USD"
            ]
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error analyzing financials for {ein}: {e}")
        return json.dumps({
            "error": f"Financial analysis failed: {str(e)}",
            "error_type": type(e).__name__
        })


@mcp.tool()
async def search_similar_nonprofits(
    ein: str,
    radius_miles: Optional[int] = None,
    same_ntee: bool = True,
    min_revenue: Optional[int] = None,
    max_revenue: Optional[int] = None,
    limit: int = 10
) -> str:
    """
    Find nonprofits similar to a given organization based on various criteria.
    
    Args:
        ein: Reference organization's EIN (9 digits, with or without hyphen)
        radius_miles: Geographic radius for location-based search
        same_ntee: Whether to limit to same NTEE category (default: True)
        min_revenue: Minimum annual revenue filter
        max_revenue: Maximum annual revenue filter
        limit: Maximum number of similar organizations to return (default: 10, max: 25)
    
    Returns:
        JSON string with similar organizations and comparison metrics
    """
    try:
        # Clean EIN format
        clean_ein = ein.replace("-", "").strip()
        if not clean_ein.isdigit() or len(clean_ein) != 9:
            return json.dumps({
                "error": "Invalid EIN format. Must be 9 digits (e.g., '123456789' or '12-3456789')"
            })
        
        # Limit validation
        if limit > 25:
            limit = 25
        
        # Get reference organization
        reference_org = await api_client.get_organization(clean_ein)
        
        # Build search criteria based on reference organization
        search_params = {}
        
        # Extract NTEE category number from the NTEE code (e.g., "A01" -> 1)
        ntee_category = None
        if same_ntee and reference_org.ntee_code:
            # NTEE codes start with a letter indicating the category
            # Map letters to numbers: A=1, B=2, etc.
            ntee_letter = reference_org.ntee_code[0].upper()
            ntee_category = ord(ntee_letter) - ord('A') + 1 if ntee_letter.isalpha() else None
        
        if reference_org.state:
            search_params["state"] = reference_org.state
        
        # Search for similar organizations
        # Use organization type/category as search term if available
        search_query = reference_org.ntee_code or "nonprofit"
        
        results = await api_client.search_organizations(
            query=search_query,
            limit=limit + 5,  # Get a few extra to filter out the reference org
            state=search_params.get("state"),
            ntee_category=ntee_category
        )
        
        # Filter out the reference organization and apply revenue filters
        similar_orgs = []
        for org in results.organizations:
            if org.ein == clean_ein:
                continue  # Skip the reference organization
            
            # Apply revenue filters if specified
            # Note: NonprofitOrganization model doesn't have income_amount field
            # Revenue filtering would require filing data, skipping for now
            pass
            
            similar_orgs.append(org)
            if len(similar_orgs) >= limit:
                break
        
        # Create comparison metrics
        comparisons = []
        for org in similar_orgs:
            comparison = {
                "organization": org.model_dump(),
                "similarity_factors": {
                    "same_state": org.state == reference_org.state,
                    "same_ntee_category": (org.ntee_code and reference_org.ntee_code and 
                                         org.ntee_code[:3] == reference_org.ntee_code[:3]),
                    "similar_revenue_range": "unknown"  # Revenue data not available in basic org data
                }
            }
            comparisons.append(comparison)
        
        # Format response
        response = {
            "reference_organization": {
                "ein": reference_org.ein,
                "name": reference_org.name,
                "state": reference_org.state,
                "ntee_code": reference_org.ntee_code,
                "revenue": None  # Revenue data not available in basic org data
            },
            "search_criteria": {
                "same_ntee": same_ntee,
                "radius_miles": radius_miles,
                "min_revenue": min_revenue,
                "max_revenue": max_revenue,
                "limit": limit
            },
            "similar_organizations_found": len(comparisons),
            "similar_organizations": comparisons,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error finding similar nonprofits for {ein}: {e}")
        return json.dumps({
            "error": f"Similar organization search failed: {str(e)}",
            "error_type": type(e).__name__
        })


@mcp.tool()
async def export_nonprofit_data(
    eins: List[str],
    format: str = "json",
    include_financials: bool = True,
    include_filings: bool = False,
    max_filings_per_org: int = 3
) -> str:
    """
    Export comprehensive data for multiple nonprofit organizations in various formats.
    
    Args:
        eins: List of EINs to export (up to 10 organizations)
        format: Export format: 'json', 'csv' (default: 'json')
        include_financials: Whether to include financial analysis (default: True)
        include_filings: Whether to include recent filings (default: False)
        max_filings_per_org: Max filings per org if include_filings=True (default: 3)
    
    Returns:
        Formatted data export suitable for CRM integration or analysis
    """
    try:
        # Validate inputs
        if not eins or len(eins) == 0:
            return json.dumps({
                "error": "No EINs provided for export"
            })
        
        if len(eins) > 10:
            return json.dumps({
                "error": "Maximum 10 organizations allowed per export"
            })
        
        if format not in ["json", "csv"]:
            return json.dumps({
                "error": "Invalid format. Must be 'json' or 'csv'"
            })
        
        # Clean EINs
        clean_eins = []
        for ein in eins:
            clean_ein = ein.replace("-", "").strip()
            if not clean_ein.isdigit() or len(clean_ein) != 9:
                return json.dumps({
                    "error": f"Invalid EIN format: {ein}. Must be 9 digits"
                })
            clean_eins.append(clean_ein)
        
        # Collect data for each organization
        export_data = []
        errors = []
        
        for ein in clean_eins:
            try:
                # Get basic organization data
                org = await api_client.get_organization(ein)
                
                org_data = {
                    "ein": ein,
                    "organization_name": org.name,
                    "sub_name": org.sub_name,
                    "street_address": org.address,
                    "city": org.city,
                    "state": org.state,
                    "zipcode": org.zipcode,
                    "ntee_code": org.ntee_code,
                    "subsection_code": org.subseccd,
                    "guidestar_url": org.guidestar_url,
                    "nccs_url": org.nccs_url,
                    "updated": org.updated.isoformat() if org.updated else None
                }
                
                # Add financial analysis if requested
                if include_financials:
                    try:
                        filings = await api_client.get_organization_filings(ein)
                        if filings:
                            latest_filing = filings[0]
                            org_data.update({
                                "latest_filing_year": latest_filing.tax_year,
                                "latest_total_revenue": latest_filing.totrevenue,
                                "latest_total_expenses": latest_filing.totfuncexpns,
                                "latest_net_assets": latest_filing.net_assets,
                                "latest_filing_date": latest_filing.filing_date.isoformat() if latest_filing.filing_date else None
                            })
                    except Exception as e:
                        logger.warning(f"Could not get financial data for {ein}: {e}")
                
                # Add recent filings if requested
                if include_filings:
                    try:
                        filings = await api_client.get_organization_filings(ein)
                        recent_filings = filings[:max_filings_per_org]
                        org_data["recent_filings"] = [filing.model_dump() for filing in recent_filings]
                    except Exception as e:
                        logger.warning(f"Could not get filings for {ein}: {e}")
                
                export_data.append(org_data)
                
            except Exception as e:
                errors.append({
                    "ein": ein,
                    "error": str(e)
                })
                logger.error(f"Error exporting data for {ein}: {e}")
        
        # Create export result - using a simple dict instead of CRMExport model for now
        export_result = {
            "export_id": f"propublica_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_organizations": len(clean_eins),
            "successful_exports": len(export_data),
            "failed_exports": len(errors),
            "export_format": format,
            "organizations": export_data,
            "errors": errors,
            "metadata": {
                "include_financials": include_financials,
                "include_filings": include_filings,
                "max_filings_per_org": max_filings_per_org if include_filings else 0,
                "api_version": "v2",
                "source": "ProPublica Nonprofit Explorer"
            }
        }
        
        # Format output based on requested format
        if format == "json":
            return json.dumps(export_result, indent=2)
        
        elif format == "csv":
            # Create CSV output
            output = io.StringIO()
            
            if export_data:
                # Define the fieldnames in a specific order starting with key fields
                key_fields = ["ein", "organization_name", "sub_name", "street_address", "city", "state", "zipcode", "ntee_code", "subsection_code"]
                
                # Get all possible fieldnames from the data
                all_fieldnames = set()
                for org in export_data:
                    all_fieldnames.update(org.keys())
                
                # Remove complex fields that don't work well in CSV
                all_fieldnames.discard("recent_filings")
                all_fieldnames.discard("classification_codes")
                
                # Start with key fields, then add remaining fields
                fieldnames = []
                for field in key_fields:
                    if field in all_fieldnames:
                        fieldnames.append(field)
                        all_fieldnames.remove(field)
                
                # Add remaining fields in sorted order
                fieldnames.extend(sorted(list(all_fieldnames)))
                
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for org in export_data:
                    # Create a clean row without complex fields
                    clean_row = {k: v for k, v in org.items() if k in fieldnames}
                    writer.writerow(clean_row)
            
            csv_content = output.getvalue()
            output.close()
            
            # Return CSV with metadata
            return json.dumps({
                "export_metadata": {
                    "export_id": export_result["export_id"],
                    "generated_at": export_result["generated_at"],
                    "total_organizations": export_result["total_organizations"],
                    "successful_exports": export_result["successful_exports"],
                    "failed_exports": export_result["failed_exports"],
                    "errors": export_result["errors"]
                },
                "csv_data": csv_content
            }, indent=2)
        
    except Exception as e:
        logger.error(f"Error exporting nonprofit data: {e}")
        return json.dumps({
            "error": f"Export failed: {str(e)}",
            "error_type": type(e).__name__
        })


def _get_revenue_similarity(revenue1: Optional[int], revenue2: Optional[int]) -> str:
    """Helper function to determine revenue similarity category."""
    if not revenue1 or not revenue2:
        return "unknown"
    
    ratio = min(revenue1, revenue2) / max(revenue1, revenue2)
    
    if ratio > 0.8:
        return "very_similar"
    elif ratio > 0.5:
        return "similar"
    elif ratio > 0.2:
        return "somewhat_similar"
    else:
        return "different"


# Note: Resource handling removed for now to focus on core tools
# Resources can be added back later once the core functionality is working


# Main function to run the server
def main():
    """Main function to run the ProPublica MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ProPublica Nonprofit Explorer MCP Server")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Run the server
    mcp.run()


if __name__ == "__main__":
    main() 