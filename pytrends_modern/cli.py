"""
Command-line interface for pytrends-modern
"""

import json
import sys
from typing import List, Optional

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress

    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False

from pytrends_modern import TrendReq, TrendsRSS
from pytrends_modern.exceptions import PyTrendsPlusError


if CLI_AVAILABLE:
    console = Console()

    def error(msg: str) -> None:
        """Print error message and exit"""
        console.print(f"[bold red]Error:[/bold red] {msg}")
        sys.exit(1)

    def success(msg: str) -> None:
        """Print success message"""
        console.print(f"[bold green]✓[/bold green] {msg}")

    def info(msg: str) -> None:
        """Print info message"""
        console.print(f"[bold blue]ℹ[/bold blue] {msg}")

    @click.group()
    @click.version_option(version="1.0.0", prog_name="pytrends-modern")
    def cli() -> None:
        """
        pytrends-modern: Modern Google Trends API

        A next-generation library combining the best features from pytrends,
        trendspyg, and more. Get interest over time, by region, related topics,
        trending searches, and real-time RSS feeds.
        """
        pass

    @cli.command()
    @click.option("--keywords", "-k", required=True, help="Comma-separated keywords (max 5)")
    @click.option("--timeframe", "-t", default="today 12-m", help='Time range (e.g., "today 12-m")')
    @click.option("--geo", "-g", default="", help='Geographic location (e.g., "US", "GB")')
    @click.option("--category", "-c", default=0, help="Category ID (0 for all)")
    @click.option(
        "--property", "-p", default="", help='Property: "", "images", "news", "youtube", "froogle"'
    )
    @click.option("--output", "-o", type=click.Path(), help="Output file path (CSV, JSON)")
    @click.option(
        "--format",
        "-f",
        type=click.Choice(["csv", "json", "table"]),
        default="table",
        help="Output format",
    )
    def interest(
        keywords: str,
        timeframe: str,
        geo: str,
        category: int,
        property: str,
        output: Optional[str],
        format: str,
    ) -> None:
        """
        Get interest over time for keywords

        Example:
            pytrends-modern interest -k "Python,JavaScript" -t "today 12-m"
        """
        try:
            # Parse keywords
            kw_list = [k.strip() for k in keywords.split(",")]

            if len(kw_list) > 5:
                error("Maximum 5 keywords allowed")

            # Initialize client
            info(f"Fetching interest over time for: {', '.join(kw_list)}")
            pytrends = TrendReq()

            # Build payload
            pytrends.build_payload(
                kw_list=kw_list, timeframe=timeframe, geo=geo, cat=category, gprop=property
            )

            # Get data
            df = pytrends.interest_over_time()

            if df.empty:
                error("No data returned. Try different keywords or timeframe.")

            # Remove isPartial column for display
            if "isPartial" in df.columns:
                df = df.drop("isPartial", axis=1)

            # Output
            if output:
                if output.endswith(".json"):
                    df.to_json(output, orient="records", date_format="iso")
                    success(f"Data saved to {output}")
                else:
                    df.to_csv(output)
                    success(f"Data saved to {output}")
            else:
                if format == "json":
                    console.print_json(df.to_json(orient="records", date_format="iso"))
                elif format == "csv":
                    console.print(df.to_csv())
                else:
                    # Display as table
                    table = Table(title=f"Interest Over Time: {', '.join(kw_list)}")
                    table.add_column("Date", style="cyan")
                    for kw in kw_list:
                        table.add_column(kw, style="magenta")

                    # Show last 10 rows
                    for idx, row in df.tail(10).iterrows():
                        table.add_row(str(idx.date()), *[str(int(row[kw])) for kw in kw_list])

                    console.print(table)
                    info(f"Showing last 10 of {len(df)} data points")

        except PyTrendsPlusError as e:
            error(str(e))
        except Exception as e:
            error(f"Unexpected error: {str(e)}")

    @cli.command()
    @click.option("--keywords", "-k", required=True, help="Comma-separated keywords")
    @click.option("--geo", "-g", default="", help="Geographic location")
    @click.option(
        "--resolution", "-r", default="COUNTRY", help="Resolution: COUNTRY, REGION, CITY, DMA"
    )
    @click.option("--output", "-o", type=click.Path(), help="Output file path")
    @click.option("--format", "-f", type=click.Choice(["csv", "json", "table"]), default="table")
    def region(
        keywords: str, geo: str, resolution: str, output: Optional[str], format: str
    ) -> None:
        """
        Get interest by region for keywords

        Example:
            pytrends-modern region -k "Python" -g "US" -r "REGION"
        """
        try:
            kw_list = [k.strip() for k in keywords.split(",")]

            info(f"Fetching interest by region for: {', '.join(kw_list)}")
            pytrends = TrendReq()

            pytrends.build_payload(kw_list=kw_list, geo=geo)
            df = pytrends.interest_by_region(resolution=resolution)

            if df.empty:
                error("No data returned")

            # Output
            if output:
                if output.endswith(".json"):
                    df.to_json(output, orient="index")
                    success(f"Data saved to {output}")
                else:
                    df.to_csv(output)
                    success(f"Data saved to {output}")
            else:
                if format == "json":
                    console.print_json(df.to_json(orient="index"))
                elif format == "csv":
                    console.print(df.to_csv())
                else:
                    # Display as table
                    table = Table(title=f"Interest by Region: {', '.join(kw_list)}")
                    table.add_column("Region", style="cyan")
                    for kw in kw_list:
                        table.add_column(kw, style="magenta")

                    # Show top 10 regions
                    df_sorted = df.sort_values(by=kw_list[0], ascending=False)
                    for region, row in df_sorted.head(10).iterrows():
                        table.add_row(str(region), *[str(int(row[kw])) for kw in kw_list])

                    console.print(table)
                    info(f"Showing top 10 of {len(df)} regions")

        except PyTrendsPlusError as e:
            error(str(e))
        except Exception as e:
            error(f"Unexpected error: {str(e)}")

    @cli.command()
    @click.option("--geo", "-g", default="US", help="Country code (e.g., US, GB, CA)")
    @click.option("--output", "-o", type=click.Path(), help="Output file path")
    @click.option("--format", "-f", type=click.Choice(["csv", "json", "table"]), default="table")
    @click.option("--images/--no-images", default=True, help="Include images")
    @click.option("--articles/--no-articles", default=True, help="Include articles")
    def rss(geo: str, output: Optional[str], format: str, images: bool, articles: bool) -> None:
        """
        Get real-time trending searches from RSS feed (fast!)

        Example:
            pytrends-modern rss -g US
            pytrends-modern rss -g GB --format json -o trends.json
        """
        try:
            info(f"Fetching RSS trends for {geo}...")

            rss_client = TrendsRSS()
            trends = rss_client.get_trends(
                geo=geo, output_format="dict", include_images=images, include_articles=articles
            )

            if not trends:
                error("No trends returned")

            # Output
            if output:
                if output.endswith(".json"):
                    with open(output, "w") as f:
                        json.dump(trends, f, indent=2, default=str)
                    success(f"Data saved to {output}")
                else:
                    # Save as CSV
                    df = rss_client.get_trends(geo=geo, output_format="dataframe")
                    df.to_csv(output, index=False)
                    success(f"Data saved to {output}")
            else:
                if format == "json":
                    console.print_json(json.dumps(trends, default=str))
                elif format == "csv":
                    df = rss_client.get_trends(geo=geo, output_format="dataframe")
                    console.print(df.to_csv(index=False))
                else:
                    # Display as table
                    table = Table(title=f"Trending Searches: {geo}")
                    table.add_column("Title", style="cyan", no_wrap=False)
                    table.add_column("Traffic", style="magenta")
                    if articles:
                        table.add_column("Articles", style="green")

                    for trend in trends[:15]:  # Show top 15
                        row = [trend.get("title", "N/A")[:60], str(trend.get("traffic", "N/A"))]
                        if articles:
                            row.append(str(trend.get("article_count", 0)))
                        table.add_row(*row)

                    console.print(table)
                    info(f"Showing {min(15, len(trends))} of {len(trends)} trends")

        except PyTrendsPlusError as e:
            error(str(e))
        except Exception as e:
            error(f"Unexpected error: {str(e)}")

    @cli.command()
    @click.option("--keyword", "-k", required=True, help="Keyword to get suggestions for")
    def suggest(keyword: str) -> None:
        """
        Get keyword suggestions from Google Trends

        Example:
            pytrends-modern suggest -k "python"
        """
        try:
            info(f"Getting suggestions for: {keyword}")
            pytrends = TrendReq()
            suggestions = pytrends.suggestions(keyword)

            if not suggestions:
                error("No suggestions found")

            table = Table(title=f"Suggestions for '{keyword}'")
            table.add_column("Title", style="cyan")
            table.add_column("Type", style="magenta")

            for suggestion in suggestions[:10]:
                table.add_row(suggestion.get("title", "N/A"), suggestion.get("type", "N/A"))

            console.print(table)

        except PyTrendsPlusError as e:
            error(str(e))
        except Exception as e:
            error(f"Unexpected error: {str(e)}")

    @cli.command()
    @click.option("--country", "-c", default="united_states", help="Country name")
    @click.option("--output", "-o", type=click.Path(), help="Output file path")
    def trending(country: str, output: Optional[str]) -> None:
        """
        Get trending searches for a country

        Example:
            pytrends-modern trending -c united_states
        """
        try:
            info(f"Getting trending searches for: {country}")
            pytrends = TrendReq()
            df = pytrends.trending_searches(pn=country)

            if df.empty:
                error("No trending searches found")

            if output:
                df.to_csv(output, index=False, header=False)
                success(f"Data saved to {output}")
            else:
                table = Table(title=f"Trending Searches: {country}")
                table.add_column("#", style="cyan")
                table.add_column("Search Term", style="magenta")

                for idx, term in enumerate(df.iloc[:, 0].head(20), 1):
                    table.add_row(str(idx), str(term))

                console.print(table)

        except PyTrendsPlusError as e:
            error(str(e))
        except Exception as e:
            error(f"Unexpected error: {str(e)}")

    def main() -> None:
        """Main entry point for CLI"""
        if not CLI_AVAILABLE:
            print("Error: CLI dependencies not installed.")
            print("Install with: pip install pytrends-modern[cli]")
            sys.exit(1)

        cli()

else:
    # CLI not available
    def main() -> None:
        """Main entry point when CLI dependencies are missing"""
        print("Error: CLI dependencies not installed.")
        print("Install with: pip install pytrends-modern[cli]")
        sys.exit(1)


if __name__ == "__main__":
    main()
