#!/usr/bin/env python3
"""
GPT Researcher Plugin - Wraps existing GPTResearcher functionality
This plugin adapts the existing GPTResearcher to work with the microkernel
"""
import sys
import json
import os
import asyncio
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add current directory to path to import existing code
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def run_research_dry(args: dict, config: dict) -> dict:
    """Dry run - simulates research without API calls"""
    
    query = args.get('query', '')
    report_type = args.get('report_type', 'research_report')
    tone = args.get('tone', 'objective')
    domains = args.get('domains', [])
    
    # Simulate research report
    mock_report = f"""# Research Report: {query}

## Executive Summary
This is a DRY RUN simulation of a research report on "{query}".

## Configuration
- Report Type: {report_type}
- Tone: {tone}
- Domains: {', '.join(domains) if domains else 'all'}
- LLM Provider: {config.get('llm_provider', 'gpt5')}
- LLM Model: {config.get('llm_model', 'gpt-5')}

## Key Findings
1. **Finding 1**: In a real run, this would contain actual research findings
2. **Finding 2**: The system would search multiple sources and synthesize information
3. **Finding 3**: Results would be formatted according to the specified tone

## Sources
- Source 1: https://example.com/article1
- Source 2: https://example.com/article2
- Source 3: https://example.com/article3

## Conclusion
This dry run demonstrates the research report structure without making actual API calls.

---
*Generated: {datetime.now().isoformat()}*
*Mode: DRY RUN*
"""
    
    # Save mock report
    output_dir = Path(config.get('output_dir', 'outputs'))
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"dry_run_{uuid4()}.md"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(mock_report)
    
    return {
        "status": "success",
        "mode": "dry_run",
        "output_path": str(output_path),
        "report_length": len(mock_report),
        "message": f"Dry run completed successfully",
        "config_used": {
            "llm_provider": config.get('llm_provider', 'gpt5'),
            "llm_model": config.get('llm_model', 'gpt-5'),
            "data_source": config.get('data_source', 'web')
        }
    }


async def run_research(args: dict, config: dict) -> dict:
    """Run research using existing GPTResearcher"""
    
    # Check for dry run
    if args.get('dry_run') or config.get('dry_run'):
        return await run_research_dry(args, config)
    
    # Import here to avoid loading if dry run
    from gpt_researcher import GPTResearcher
    from gpt_researcher.utils.enum import ReportType, Tone
    from backend.report_type import DetailedReport
    
    # Extract arguments
    query = args.get('query', '')
    report_type = args.get('report_type', 'research_report')
    tone_str = args.get('tone', 'objective')
    domains = args.get('domains', [])
    
    # Map tone string to enum
    tone_map = {
        "objective": Tone.Objective,
        "formal": Tone.Formal,
        "analytical": Tone.Analytical,
        "persuasive": Tone.Persuasive,
        "informative": Tone.Informative,
        "explanatory": Tone.Explanatory,
        "descriptive": Tone.Descriptive,
        "critical": Tone.Critical,
        "comparative": Tone.Comparative,
        "speculative": Tone.Speculative,
        "reflective": Tone.Reflective,
        "narrative": Tone.Narrative,
        "humorous": Tone.Humorous,
        "optimistic": Tone.Optimistic,
        "pessimistic": Tone.Pessimistic
    }
    
    tone = tone_map.get(tone_str, Tone.Objective)
    
    # Set LLM provider environment variables
    if config.get('llm_provider') == 'gpt5':
        os.environ['OPENAI_API_MODEL'] = config.get('llm_model', 'gpt-5')
    
    try:
        if report_type == 'detailed_report':
            detailed_report = DetailedReport(
                query=query,
                query_domains=domains,
                report_type="research_report",
                report_source="web_search",
            )
            report = await detailed_report.run()
        else:
            researcher = GPTResearcher(
                query=query,
                query_domains=domains,
                report_type=report_type,
                tone=tone,
            )
            await researcher.conduct_research()
            report = await researcher.write_report()
        
        # Save report
        output_dir = Path(config.get('output_dir', 'outputs'))
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{uuid4()}.md"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        return {
            "status": "success",
            "mode": "live",
            "output_path": str(output_path),
            "report_length": len(report),
            "message": f"Research completed successfully",
            "config_used": {
                "llm_provider": config.get('llm_provider', 'gpt5'),
                "llm_model": config.get('llm_model', 'gpt-5'),
                "data_source": config.get('data_source', 'web')
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Research failed",
            "hint": "Try running with --dry-run to test the setup"
        }


def main():
    """Plugin entry point"""
    
    # Read input from kernel
    try:
        input_data = json.loads(sys.stdin.read())
    except Exception as e:
        error = {"status": "error", "error": f"Failed to parse input: {e}"}
        print(json.dumps(error), file=sys.stderr)
        return 1
    
    # Extract data
    args = input_data.get('args', {})
    config = input_data.get('config', {})
    
    # Run async research
    try:
        result = asyncio.run(run_research(args, config))
        print(json.dumps(result, indent=2))
        return 0 if result['status'] == 'success' else 1
    except Exception as e:
        error = {"status": "error", "error": str(e)}
        print(json.dumps(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())