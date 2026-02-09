import asyncio
import sys
import codecs
from config import AgentConfig
from agents.research_agent import ResearchAgent
import json
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Fix Unicode encoding for Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

console = Console(force_terminal=True, legacy_windows=False)


async def main():
    """Main application"""
    
    # Initialize
    console.print(Panel.fit(
        "🤖 [bold blue]AI Research Assistant[/bold blue]\n"
        "Production-level Agent với LCEL",
        border_style="blue"
    ))
    
    config = AgentConfig()
    agent = ResearchAgent(config)
    
    # Example research queries
    queries = [
        "What are the latest breakthroughs in quantum computing in 2024? Compare different approaches.",
        "Analyze the economic impact of AI on job markets. Use multiple sources.",
        "What is LCEL in LangChain? Provide technical details and examples."
    ]
    
    console.print("\n[bold green]Example Queries:[/bold green]")
    for i, q in enumerate(queries, 1):
        console.print(f"{i}. {q}")
    
    console.print("\n[yellow]Enter your query (or choose 1-3, or 'quit' to exit):[/yellow]")
    
    while True:
        user_input = input("\n> ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            console.print("[bold red]Goodbye![/bold red]")
            break
        
        # Handle numeric selection
        if user_input.isdigit() and 1 <= int(user_input) <= len(queries):
            query = queries[int(user_input) - 1]
        else:
            query = user_input
        
        if not query:
            continue
        
        # Run research with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🔍 Researching...", total=None)
            
            result = await agent.research(
                query=query,
                enable_deep_analysis=True
            )
        
        # Display results
        if result["success"]:
            console.print("\n" + "="*60)
            console.print(Panel(
                Markdown(result["answer"]),
                title="[bold green]Research Results[/bold green]",
                border_style="green"
            ))
            
            # Metadata
            console.print(f"\n[dim]⏱️  Execution time: {result['execution_time']:.2f}s[/dim]")
            console.print(f"[dim]🔧 Intermediate steps: {result['intermediate_steps']}[/dim]")
            
            # Analysis insights
            if result.get("analysis", {}).get("structured"):
                analysis = result["analysis"]["structured"]
                # Convert Pydantic model to dict if needed
                if hasattr(analysis, 'dict'):
                    analysis = analysis.dict()
                elif hasattr(analysis, 'model_dump'):
                    analysis = analysis.model_dump()
                
                console.print(f"\n[bold cyan]Analysis Insights:[/bold cyan]")
                console.print(f"  • Confidence: {analysis.get('confidence_score', 0):.2%}")
                console.print(f"  • Data Quality: {analysis.get('data_quality', 'unknown')}")
                
                if analysis.get('key_findings'):
                    console.print(f"\n[bold]Key Findings:[/bold]")
                    for finding in analysis['key_findings'][:3]:
                        console.print(f"  • {finding}")
        else:
            console.print(f"\n[bold red]Error:[/bold red] {result.get('error', 'Unknown error')}")
        
        # Memory stats
        stats = agent.get_memory_stats()
        console.print(f"\n[dim]💾 Memory: {stats['short_term_messages']} recent messages, "
                     f"{stats['long_term_documents']} stored interactions[/dim]")


def run_single_query():
    """Helper function to run a single query"""
    async def _run():
        config = AgentConfig()
        agent = ResearchAgent(config)
        
        query = "Cơ hội và việc làm trong lĩnh vực STEM ở việt nam năm 2025"
        
        console.print(f"\n[bold]Query:[/bold] {query}\n")
        
        result = await agent.research(query, enable_deep_analysis=True)
        
        if result["success"]:
            console.print(Panel(
                Markdown(result["answer"]),
                title="Answer",
                border_style="green"
            ))
            
            # Save to file
            with open("research_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            console.print("\n[green]✓ Results saved to research_result.json[/green]")
        
    asyncio.run(_run())


if __name__ == "__main__":
    # Interactive mode
    # asyncio.run(main())
    
    # Or single query mode:
    run_single_query()