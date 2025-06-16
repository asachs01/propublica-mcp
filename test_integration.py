#!/usr/bin/env python3
"""
ProPublica MCP Integration Test

This script performs basic integration testing to verify that the MCP server
and API client work correctly with real API calls (or mocked ones).
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from propublica_mcp.api_client import ProPublicaClient
from propublica_mcp.server import (
    search_nonprofits,
    get_organization,
    get_organization_filings
)


async def test_api_client():
    """Test the API client with a real API call."""
    print("🔍 Testing API Client...")
    
    try:
        client = ProPublicaClient()
        
        # Test a basic search
        results = await client.search_organizations(
            query="red cross",
            limit=2
        )
        
        print(f"✅ API Search successful: {len(results.organizations)} organizations found")
        print(f"   Total results available: {results.total_results}")
        
        if results.organizations:
            org = results.organizations[0]
            print(f"   First organization: {org.name} (EIN: {org.ein})")
            
            # Test getting detailed organization info
            detailed_org = await client.get_organization(org.ein)
            print(f"✅ Organization details retrieved: {detailed_org.name}")
            
            # Test getting filings (limit to 1 for speed)
            filings = await client.get_organization_filings(org.ein)
            print(f"✅ Filings retrieved: {len(filings)} filings found")
            
        return True
        
    except Exception as e:
        print(f"❌ API Client test failed: {e}")
        return False


async def test_mcp_tools():
    """Test the MCP tools (these will make real API calls)."""
    print("\n🛠️  Testing MCP Tools...")
    
    try:
        # Test search tool
        result = await search_nonprofits(
            query="american cancer society",
            per_page=2
        )
        result_data = json.loads(result)
        
        if "error" in result_data:
            print(f"❌ Search tool failed: {result_data['error']}")
            return False
            
        print(f"✅ Search tool successful: {len(result_data['organizations'])} organizations")
        
        if result_data['organizations']:
            # Test get organization tool
            ein = result_data['organizations'][0]['ein']
            org_result = await get_organization(ein=ein)
            org_data = json.loads(org_result)
            
            if "error" in org_data:
                print(f"❌ Get organization tool failed: {org_data['error']}")
                return False
                
            print(f"✅ Get organization tool successful: {org_data['organization']['name']}")
            
            # Test get filings tool (limit to 1 for speed)
            filings_result = await get_organization_filings(ein=ein, limit=1)
            filings_data = json.loads(filings_result)
            
            if "error" in filings_data:
                print(f"❌ Get filings tool failed: {filings_data['error']}")
                return False
                
            print(f"✅ Get filings tool successful: {filings_data['filings_returned']} filings")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP Tools test failed: {e}")
        return False


def test_data_models():
    """Test that data models can be imported and instantiated."""
    print("\n📋 Testing Data Models...")
    
    try:
        from propublica_mcp.models import (
            NonprofitOrganization,
            Filing,
            SearchResult,
            FinancialSummary,
            CRMExport,
            NTEE_CATEGORIES,
            SUBSECTION_CODES
        )
        
        # Test that validation constants are populated
        assert len(NTEE_CATEGORIES) > 0, "NTEE categories should be populated"
        assert len(SUBSECTION_CODES) > 0, "Subsection codes should be populated"
        
        print(f"✅ Data models imported successfully")
        print(f"   NTEE categories: {len(NTEE_CATEGORIES)}")
        print(f"   Subsection codes: {len(SUBSECTION_CODES)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data models test failed: {e}")
        return False


def test_configuration():
    """Test that configuration files exist and are valid."""
    print("\n⚙️  Testing Configuration...")
    
    try:
        # Check config file
        config_path = Path("config/propublica_mcp_config.json")
        if not config_path.exists():
            print(f"❌ Config file not found: {config_path}")
            return False
            
        with open(config_path) as f:
            config = json.load(f)
            
        assert "mcpServers" in config, "Config should have mcpServers section"
        assert "propublica-mcp" in config["mcpServers"], "Config should have propublica-mcp server"
        
        print("✅ Configuration file is valid")
        
        # Check requirements file
        req_path = Path("requirements.txt")
        if not req_path.exists():
            print(f"❌ Requirements file not found: {req_path}")
            return False
            
        with open(req_path) as f:
            requirements = f.read()
            
        assert "fastmcp" in requirements.lower(), "FastMCP should be in requirements"
        assert "httpx" in requirements.lower(), "httpx should be in requirements"
        assert "pydantic" in requirements.lower(), "Pydantic should be in requirements"
        
        print("✅ Requirements file contains expected dependencies")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print("🚀 ProPublica MCP Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Data Models", test_data_models),
    ]
    
    # Only run API tests if we're in an environment where they should work
    if os.getenv("RUN_API_TESTS", "false").lower() == "true":
        tests.extend([
            ("API Client", test_api_client),
            ("MCP Tools", test_mcp_tools),
        ])
    else:
        print("ℹ️  Skipping API tests (set RUN_API_TESTS=true to enable)")
    
    results = []
    
    for test_name, test_func in tests:
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The ProPublica MCP server is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 