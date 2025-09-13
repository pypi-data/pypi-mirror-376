#!/usr/bin/env python3
"""
Web Search Tool Examples for TNSA API Python SDK

Demonstrates the web search capabilities integrated with AI models.
"""

import os
import asyncio
from tnsa_api import TNSA, web_search, web_search_summary, DuckDuckGoSearchTool

def basic_web_search_example():
    """Basic web search example."""
    print("🔍 Basic Web Search Example")
    print("=" * 50)
    
    try:
        # Direct web search
        print("📡 Performing direct web search...")
        results = web_search("Python programming latest features 2024")
        
        print(f"✅ Search completed for: {results['query']}")
        print(f"📊 Total results: {results['total_results']}")
        
        if results.get("abstract"):
            print(f"📝 Summary: {results['abstract']}")
        
        if results.get("answer"):
            print(f"💡 Answer: {results['answer']}")
        
        if results.get("related"):
            print(f"🔗 Related topics ({len(results['related'])}):")
            for i, topic in enumerate(results['related'][:3], 1):
                print(f"   {i}. {topic['text']}")
        
        # Get summary
        print("\n📋 Getting search summary...")
        summary = web_search_summary("Python programming latest features 2024", max_length=300)
        print(f"Summary: {summary}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def ai_enhanced_search_example():
    """AI model enhanced with web search."""
    print("\n🤖 AI Enhanced with Web Search Example")
    print("=" * 50)
    
    # Configure with web search enabled
    client = TNSA(
        api_key=os.getenv("TNSA_API_KEY", "demo-key"),
        base_url=os.getenv("TNSA_BASE_URL", "http://demo.api"),
        web_search_enabled=True  # Enable web search
    )
    
    try:
        # This will automatically trigger web search due to keywords
        print("🔍 Asking AI about recent developments...")
        response = client.chat.completions.create(
            model="NGen3.9-Pro",
            messages=[
                {"role": "user", "content": "What are the latest developments in AI and machine learning in 2024?"}
            ],
            enable_web_search=True  # Explicitly enable for this request
        )
        
        print("✅ AI Response with web search enhancement:")
        print(response.choices[0].message.content)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

def manual_search_integration_example():
    """Manual integration of web search with AI."""
    print("\n🔧 Manual Search Integration Example")
    print("=" * 50)
    
    client = TNSA(
        api_key=os.getenv("TNSA_API_KEY", "demo-key"),
        base_url=os.getenv("TNSA_BASE_URL", "http://demo.api"),
        web_search_enabled=True
    )
    
    try:
        # Manual web search
        print("🔍 Performing manual web search...")
        search_results = client.web_search.search("quantum computing breakthroughs 2024")
        
        # Create enhanced prompt
        search_summary = client.web_search.search_tool.summarize_results(search_results, 400)
        enhanced_prompt = f"""
Based on the following recent web search results about quantum computing:

{search_summary}

Please provide a comprehensive analysis of the current state of quantum computing and its potential impact on various industries.
"""
        
        print("🤖 Asking AI with search-enhanced prompt...")
        response = client.chat.completions.create(
            model="NGen3.9-Pro",
            messages=[
                {"role": "user", "content": enhanced_prompt}
            ],
            enable_web_search=False  # Disable auto-search since we already did it
        )
        
        print("✅ AI Response with manual search integration:")
        print(response.choices[0].message.content)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

def advanced_search_tool_example():
    """Advanced search tool usage."""
    print("\n⚙️ Advanced Search Tool Example")
    print("=" * 50)
    
    try:
        with DuckDuckGoSearchTool(timeout=15.0) as search_tool:
            # Multiple searches with different configurations
            queries = [
                ("artificial intelligence ethics", 5, True),
                ("climate change solutions 2024", 8, False),
                ("space exploration news", 3, True)
            ]
            
            for query, max_results, include_related in queries:
                print(f"\n🔍 Searching: {query}")
                results = search_tool.search(
                    query=query,
                    max_results=max_results,
                    include_related=include_related,
                    safe_search="moderate"
                )
                
                print(f"   📊 Results: {results['total_results']}")
                if results.get("heading"):
                    print(f"   📌 Topic: {results['heading']}")
                if results.get("abstract"):
                    print(f"   📝 Summary: {results['abstract'][:100]}...")
                
                # Generate summary
                summary = search_tool.summarize_results(results, 200)
                print(f"   📋 AI Summary: {summary[:150]}...")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def configuration_example():
    """Web search configuration example."""
    print("\n⚙️ Web Search Configuration Example")
    print("=" * 50)
    
    # Show different configuration options
    configs = [
        {
            "name": "Default Config",
            "web_search_enabled": True,
        },
        {
            "name": "High Performance Config", 
            "web_search_enabled": True,
            "web_search_timeout": 5.0,
            "web_search_max_results": 15,
            "web_search_safe_search": "moderate"
        },
        {
            "name": "Conservative Config",
            "web_search_enabled": True,
            "web_search_timeout": 20.0,
            "web_search_max_results": 5,
            "web_search_safe_search": "strict"
        }
    ]
    
    for config_info in configs:
        print(f"\n📋 {config_info['name']}:")
        
        # Create client with specific config
        client = TNSA(
            api_key=os.getenv("TNSA_API_KEY", "demo-key"),
            base_url=os.getenv("TNSA_BASE_URL", "http://demo.api"),
            **{k: v for k, v in config_info.items() if k != "name"}
        )
        
        try:
            # Show configuration
            config_dict = client.config.to_dict()
            print(f"   Web Search Enabled: {config_dict['web_search_enabled']}")
            print(f"   Timeout: {config_dict.get('web_search_timeout', 'default')}s")
            print(f"   Max Results: {config_dict.get('web_search_max_results', 'default')}")
            print(f"   Safe Search: {config_dict.get('web_search_safe_search', 'default')}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        finally:
            client.close()

async def async_search_example():
    """Async web search example (placeholder)."""
    print("\n⚡ Async Web Search Example")
    print("=" * 50)
    
    # Note: This is a placeholder for future async implementation
    print("🚧 Async web search will be implemented in future versions")
    print("   For now, use the synchronous web search functionality")

def main():
    """Run all web search examples."""
    print("🌐 TNSA API Web Search Tool Examples")
    print("=" * 60)
    print("Demonstrating web search integration with AI models")
    
    # Set environment variables for demo
    if not os.getenv("TNSA_API_KEY"):
        os.environ["TNSA_API_KEY"] = "demo-key"
    if not os.getenv("TNSA_BASE_URL"):
        os.environ["TNSA_BASE_URL"] = "http://demo.api"
    
    try:
        # Run examples
        basic_web_search_example()
        ai_enhanced_search_example()
        manual_search_integration_example()
        advanced_search_tool_example()
        configuration_example()
        
        # Run async example
        asyncio.run(async_search_example())
        
        print("\n🎊 All web search examples completed!")
        print("\n💡 Key Features Demonstrated:")
        print("   • Direct web search with DuckDuckGo")
        print("   • Automatic AI prompt enhancement")
        print("   • Manual search integration")
        print("   • Advanced search configurations")
        print("   • Error handling and fallbacks")
        print("   • Search result summarization")
        
        print("\n🚀 Ready for production use!")
        
    except KeyboardInterrupt:
        print("\n🛑 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()