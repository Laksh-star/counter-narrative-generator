#!/usr/bin/env python3
"""
Counter-Narrative Generator CLI

A Panchatantra Three-Fish framework for mining contrarian wisdom from Lenny's Podcast.

Usage:
    python main.py load                    # Load chunks into ChromaDB
    python main.py query "Your belief"     # Find contrarian perspectives
    python main.py stats                   # Show vector store stats
    python main.py interactive             # Interactive mode
"""

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import config
from src.data.vectorstore import VectorStore
from src.workflow import CounterNarrativeWorkflow, format_report_text

app = typer.Typer(
    name="counter-narrative",
    help="Mine contrarian wisdom from Lenny's Podcast using the Panchatantra Three-Fish framework."
)
console = Console()


def get_vectorstore() -> VectorStore:
    """Get or create the vector store"""
    return VectorStore(persist_directory=config.chroma.persist_directory)


@app.command()
def load(
    force: bool = typer.Option(False, "--force", "-f", help="Force reload even if data exists"),
    chunks_path: str = typer.Option(None, "--chunks", "-c", help="Path to chunks.jsonl"),
):
    """Load podcast chunks into ChromaDB vector store"""
    console.print("\n[bold blue]📚 Loading Lenny's Podcast chunks into ChromaDB...[/bold blue]\n")

    path = chunks_path or config.chunks_path

    if not Path(path).exists():
        console.print(f"[red]Error: Chunks file not found at {path}[/red]")
        raise typer.Exit(1)

    vectorstore = get_vectorstore()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Loading and embedding chunks...", total=None)
        count = vectorstore.load_chunks(path, force_reload=force)

    console.print(f"\n[green]✅ Loaded {count:,} chunks into ChromaDB[/green]")
    console.print(f"   Persist directory: {config.chroma.persist_directory}")


@app.command()
def stats():
    """Show statistics about the vector store"""
    console.print("\n[bold blue]📊 Vector Store Statistics[/bold blue]\n")

    vectorstore = get_vectorstore()
    stats = vectorstore.get_stats()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Chunks", f"{stats['total_chunks']:,}")
    table.add_row("Sample Size", f"{stats['sample_size']:,}")
    table.add_row("With Contrarian Signals (in sample)", f"{stats['contrarian_in_sample']:,}")

    console.print(table)

    if stats['topic_distribution']:
        console.print("\n[bold]Topic Distribution (top 10):[/bold]")
        topic_table = Table(show_header=True, header_style="bold magenta")
        topic_table.add_column("Topic", style="cyan")
        topic_table.add_column("Count", style="green")

        for topic, count in list(stats['topic_distribution'].items())[:10]:
            topic_table.add_row(topic, str(count))

        console.print(topic_table)


@app.command()
def query(
    belief: str = typer.Argument(..., help="The conventional wisdom to challenge"),
    topics: str = typer.Option(None, "--topics", "-t", help="Comma-separated topics to filter by"),
    results: int = typer.Option(5, "--results", "-n", help="Number of contrarian perspectives to find"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path (JSON)"),
    save: bool = typer.Option(False, "--save", "-s", help="Auto-save results to outputs/ directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed progress"),
):
    """Find contrarian perspectives on a conventional belief"""

    console.print(Panel(
        f'[bold]Challenging:[/bold] "{belief}"',
        title="🎯 Counter-Narrative Generator",
        border_style="blue"
    ))

    # Check if API key is set
    if not config.models.api_key:
        console.print("\n[red]Error: OPENROUTER_API_KEY not set[/red]")
        console.print("Set it in .env file or as environment variable")
        raise typer.Exit(1)

    # Parse topics
    filter_topics = [t.strip() for t in topics.split(",")] if topics else None

    # Initialize
    vectorstore = get_vectorstore()

    # Check if vectorstore has data
    if vectorstore.collection.count() == 0:
        console.print("\n[red]Error: Vector store is empty. Run 'python main.py load' first.[/red]")
        raise typer.Exit(1)

    workflow = CounterNarrativeWorkflow(vectorstore)

    # Run workflow
    console.print("\n[dim]Running Three-Fish workflow...[/dim]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=verbose,  # Disable progress bar in verbose mode
    ) as progress:
        if not verbose:
            task = progress.add_task("Processing...", total=None)

        result = workflow.run(
            conventional_wisdom=belief,
            filter_topics=filter_topics,
            n_contrarian_results=results,
            verbose=verbose,
        )

    # Output
    if result.success:
        report_text = format_report_text(result)
        console.print(report_text)

        # Show token usage
        total_tokens = result.total_tokens["prompt"] + result.total_tokens["completion"]
        console.print(f"\n[dim]Tokens used: {total_tokens:,} | Time: {result.execution_time_ms}ms[/dim]")

        # Save to file if requested
        if output:
            with open(output, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            console.print(f"\n[green]Saved full results to {output}[/green]")

        # Auto-save if --save flag is set
        if save:
            import os
            from datetime import datetime

            # Create outputs directory if it doesn't exist
            os.makedirs("outputs", exist_ok=True)

            # Generate filename from belief
            safe_belief = "".join(c if c.isalnum() or c in " -_" else "" for c in belief)[:50]
            safe_belief = safe_belief.strip().replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"outputs/{timestamp}_{safe_belief}.json"

            with open(filename, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            console.print(f"\n[green]Auto-saved results to {filename}[/green]")
    else:
        console.print(f"\n[red]Workflow failed with errors:[/red]")
        for error in result.errors:
            console.print(f"  • {error}")


@app.command()
def interactive():
    """Interactive mode for exploring contrarian perspectives"""

    console.print(Panel(
        "[bold]Counter-Narrative Generator[/bold]\n\n"
        "Enter a conventional wisdom to challenge, or type 'quit' to exit.\n"
        "Type 'examples' to see sample queries.",
        title="🐟 Panchatantra Three-Fish Framework",
        border_style="blue"
    ))

    # Check setup
    if not config.models.api_key:
        console.print("\n[red]Error: OPENROUTER_API_KEY not set[/red]")
        raise typer.Exit(1)

    vectorstore = get_vectorstore()
    if vectorstore.collection.count() == 0:
        console.print("\n[red]Error: Vector store is empty. Run 'python main.py load' first.[/red]")
        raise typer.Exit(1)

    workflow = CounterNarrativeWorkflow(vectorstore)

    examples = [
        "Everyone says you need product-market fit before scaling",
        "You should always listen to what your users want",
        "Hiring fast is key to startup success",
        "Data-driven decisions are always better than intuition",
        "You need to raise VC money to build a successful startup",
        "Remote work is less productive than in-office work",
        "You should focus on one thing and do it well",
    ]

    while True:
        console.print("\n")
        belief = console.input("[bold cyan]Conventional wisdom to challenge:[/bold cyan] ").strip()

        if belief.lower() == 'quit':
            console.print("\n[dim]Goodbye! 🐟🐟🐟[/dim]")
            break

        if belief.lower() == 'examples':
            console.print("\n[bold]Example queries:[/bold]")
            for i, ex in enumerate(examples, 1):
                console.print(f"  {i}. {ex}")
            continue

        if not belief:
            continue

        # Check if it's a number (selecting from examples)
        if belief.isdigit():
            idx = int(belief) - 1
            if 0 <= idx < len(examples):
                belief = examples[idx]
                console.print(f"[dim]Selected: {belief}[/dim]")
            else:
                console.print("[yellow]Invalid example number[/yellow]")
                continue

        console.print("\n[dim]Running Three-Fish workflow...[/dim]")

        result = workflow.run(
            conventional_wisdom=belief,
            verbose=True,
        )

        if result.success:
            report_text = format_report_text(result)
            console.print(report_text)

            # Offer to save
            save_choice = console.input("\n[dim]Save results? (y/n/filename): [/dim]").strip().lower()
            if save_choice == 'y':
                import os
                from datetime import datetime

                os.makedirs("outputs", exist_ok=True)
                safe_belief = "".join(c if c.isalnum() or c in " -_" else "" for c in belief)[:50]
                safe_belief = safe_belief.strip().replace(" ", "_")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"outputs/{timestamp}_{safe_belief}.json"

                with open(filename, 'w') as f:
                    json.dump(result.to_dict(), f, indent=2)
                console.print(f"[green]Saved to {filename}[/green]")
            elif save_choice and save_choice != 'n':
                # User provided a filename
                filename = save_choice if save_choice.endswith('.json') else f"{save_choice}.json"
                with open(filename, 'w') as f:
                    json.dump(result.to_dict(), f, indent=2)
                console.print(f"[green]Saved to {filename}[/green]")
        else:
            console.print(f"\n[red]Failed:[/red] {', '.join(result.errors)}")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    n: int = typer.Option(5, "-n", help="Number of results"),
    contrarian: bool = typer.Option(False, "--contrarian", "-c", help="Prefer contrarian content"),
):
    """Direct search of the vector store (for debugging)"""

    vectorstore = get_vectorstore()

    if contrarian:
        results = vectorstore.search_contrarian(query, n_results=n)
    else:
        results = vectorstore.search(query, n_results=n)

    console.print(f"\n[bold]Search results for:[/bold] {query}\n")

    for i, r in enumerate(results, 1):
        console.print(Panel(
            f"[bold]{r['guest']}[/bold] [{r['citation']}]\n\n"
            f"{r['text'][:500]}...\n\n"
            f"[dim]Similarity: {r['similarity']:.3f} | "
            f"Contrarian: {'Yes' if r['has_contrarian_signal'] else 'No'}[/dim]",
            title=f"Result {i}",
            border_style="green" if r['has_contrarian_signal'] else "blue"
        ))


if __name__ == "__main__":
    app()
