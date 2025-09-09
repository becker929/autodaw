"""Display utilities for JSI demo."""

from typing import List, Optional, Dict
from rich.table import Table
from rich.panel import Panel


def create_ranking_table(ranking: List[str], strengths: Optional[Dict[str, float]] = None,
                        title: str = "CURRENT RANKING") -> Table:
    """Create a Rich table for ranking display.

    Args:
        ranking: List of items in ranked order
        strengths: Optional dictionary of item strengths
        title: Table title

    Returns:
        Rich Table object
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="dim", width=4)
    table.add_column("Item", style="bold", width=15)
    if strengths:
        table.add_column("Strength", style="cyan", width=12)

    for i, item in enumerate(ranking, 1):
        if strengths:
            strength_str = f"~{strengths[item]:.3f}"
            table.add_row(str(i), item, strength_str)
        else:
            table.add_row(str(i), item)

    return table


def create_stats_panel(comparisons_made: int, elapsed_time: Optional[float] = None,
                      top_item: Optional[str] = None, confidence: Optional[float] = None) -> Panel:
    """Create a Rich panel for session statistics.

    Args:
        comparisons_made: Number of comparisons made
        elapsed_time: Optional elapsed time in seconds
        top_item: Optional name of top-ranked item
        confidence: Optional confidence score

    Returns:
        Rich Panel object
    """
    stats_text = f"Comparisons: {comparisons_made}\n"
    if elapsed_time:
        stats_text += f"Elapsed: {elapsed_time:.1f}s\n"
    if top_item:
        stats_text += f"Top item: {top_item}\n"
    if confidence is not None:
        stats_text += f"Confidence: {confidence:.1%}"

    return Panel(stats_text, title="Session Stats", border_style="blue")
