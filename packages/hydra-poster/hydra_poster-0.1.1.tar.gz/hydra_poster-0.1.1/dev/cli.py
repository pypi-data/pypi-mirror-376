#!/usr/bin/env python3
# type: ignore
"""Professional CLI tool for testing social media posting library.

Usage examples:
    uv run manual_test.py twitter "Hello world!"
    uv run manual_test.py linkedin "My post" --threaded
    uv run manual_test.py bluesky "Check this out" --image=1 --image=2
    uv run manual_test.py reddit "Test post" --subreddit=python --title="My Title"
    uv run manual_test.py reddit "Link post" --subreddit=test --title="Check this out" --url="https://example.com"
    uv run manual_test.py all "Cross-platform test" --cleanup
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hydra_poster import (
    BlueSkyService,
    LinkedInService,
    MediaItem,
    PostConfig,
    RedditService,
    TwitterService,
)

app = typer.Typer(
    name="social-media-test",
    help="Professional CLI for testing social media posting library",
    rich_markup_mode="rich",
    epilog="Run 'uv run test.py examples' to see usage examples, or see dev/README.md for full documentation.",
)
console = Console()


# Platform type definitions
class Platform(str, Enum):
    twitter = "twitter"
    bluesky = "bluesky"
    linkedin = "linkedin"
    reddit = "reddit"
    all = "all"


class Config:
    """Configuration manager for the CLI."""

    def __init__(self, config_path: Path = Path("config.json")):
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self):
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            console.print(f"[red]Config file not found: {self.config_path}[/]")
            console.print("[yellow]Create config.json from config.example.json[/]")
            raise typer.Exit(1)

        try:
            with open(self.config_path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            console.print(f"[red]Failed to load config: {e}[/]")
            raise typer.Exit(1) from e

    def get_platform_config(self, platform: str):
        """Get configuration for a specific platform."""
        return self._config.get("platforms", {}).get(platform, {})

    def get_setting(self, key: str, default=None):
        """Get a global setting."""
        return self._config.get("settings", {}).get(key, default)

    def get_image_path(self, index: int) -> Path | None:
        """Get image path by index (1-based)."""
        images = self._config.get("images", {})

        if index == 1:
            # Single image
            single = images.get("single")
            if single and Path(single).exists():
                return Path(single)

        # Multi images (1-based indexing)
        multi = images.get("multi", [])
        if 1 <= index <= len(multi):
            path = Path(multi[index - 1])
            if path.exists():
                return path

        return None

    def get_document_path(self, doc_type: str = "test_pdf") -> Path | None:
        """Get document path by type."""
        docs = self._config.get("documents", {})
        doc_path = docs.get(doc_type)
        if doc_path and Path(doc_path).exists():
            return Path(doc_path)
        return None


def create_service(platform: str, config: Config):
    """Create a service instance for the given platform."""
    platform_config = config.get_platform_config(platform)

    if not platform_config:
        console.print(f"[red]No configuration found for {platform}[/]")
        return None

    try:
        if platform == "twitter":
            bearer_token = platform_config.get("bearer_token")
            if not bearer_token:
                console.print("[red]Twitter bearer_token not configured[/]")
                return None
            return TwitterService(bearer_token)

        elif platform == "bluesky":
            handle = platform_config.get("handle")
            password = platform_config.get("password")
            if not handle or not password:
                console.print("[red]Bluesky handle and password must be configured[/]")
                return None
            return BlueSkyService(handle, password)

        elif platform == "linkedin":
            access_token = platform_config.get("access_token")
            person_urn = platform_config.get("person_urn")
            if not access_token or not person_urn:
                console.print(
                    "[red]LinkedIn access_token and person_urn must be configured[/]"
                )
                return None
            return LinkedInService(access_token, person_urn)

        elif platform == "reddit":
            access_token = platform_config.get("access_token")
            user_agent = platform_config.get("user_agent")
            if not access_token or not user_agent:
                console.print(
                    "[red]Reddit access_token and user_agent must be configured[/]"
                )
                return None
            return RedditService(access_token, user_agent)

    except Exception as e:
        console.print(f"[red]Failed to create {platform} service: {e}[/]")
        return None


def make_unique_message(message: str, config: Config) -> str:
    """Add timestamp and test prefix to make message unique."""
    prefix = config.get_setting("test_prefix", "[TEST]")
    timestamp = datetime.now().strftime("%H:%M:%S")
    return f"{prefix} {message} (test at {timestamp})"


def collect_images(image_indices: list[int], config: Config) -> list[MediaItem]:
    """Collect media items from image indices."""
    media_items = []

    for i, index in enumerate(image_indices, 1):
        image_path = config.get_image_path(index)
        if image_path:
            alt_text = (
                f"Test image {i} of {len(image_indices)}"
                if len(image_indices) > 1
                else "Test image"
            )
            media_items.append(MediaItem(str(image_path), "image", alt_text=alt_text))
        else:
            console.print(f"[yellow]Warning: Image {index} not found, skipping[/]")

    return media_items


@app.command()
def post(
    platform: Annotated[
        Platform,
        typer.Argument(
            help="Platform to post to (or 'all' for all configured platforms)"
        ),
    ],
    message: Annotated[str, typer.Argument(help="Message content to post")],
    threaded: Annotated[
        bool,
        typer.Option(
            "--threaded", "-t", help="Create a thread/series instead of single post"
        ),
    ] = False,
    image: Annotated[
        list[int] | None,
        typer.Option(
            "--image", "-i", help="Image index to include (can be used multiple times)"
        ),
    ] = None,
    document: Annotated[
        bool,
        typer.Option(
            "--document", "-d", help="Include a test document (LinkedIn only)"
        ),
    ] = False,
    subreddit: Annotated[
        str | None,
        typer.Option(
            "--subreddit", "-s", help="Reddit subreddit (required for Reddit)"
        ),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option("--title", help="Reddit post title (required for Reddit)"),
    ] = None,
    url: Annotated[
        str | None, typer.Option("--url", "-u", help="URL for link posts (Reddit)")
    ] = None,
    cleanup: Annotated[
        bool, typer.Option("--cleanup", "-c", help="Delete posts after creation")
    ] = False,
    config_file: Annotated[
        Path, typer.Option("--config", help="Config file path")
    ] = Path("config.json"),
) -> None:
    """Post a message to social media platform(s)."""

    # Load configuration
    config = Config(config_file)

    # Handle "all" platform
    platforms_to_test = []
    if platform == Platform.all:
        # Test all configured platforms
        for p in ["twitter", "bluesky", "linkedin", "reddit"]:
            if config.get_platform_config(p):
                platforms_to_test.append(p)
        if not platforms_to_test:
            console.print("[red]No platforms configured![/]")
            raise typer.Exit(1)
    else:
        platforms_to_test = [platform.value]

    # Collect media
    media_items = []
    if image:
        media_items = collect_images(image, config)
        if not media_items:
            console.print("[yellow]No valid images found[/]")

    # Collect document (LinkedIn only)
    document_item = None
    if document:
        doc_path = config.get_document_path()
        if doc_path:
            document_item = MediaItem(
                str(doc_path), "document", alt_text="Test document"
            )
        else:
            console.print("[yellow]No valid document found[/]")

    # Results tracking
    results = {}
    created_posts = {}  # For cleanup

    # Process each platform
    for platform_name in platforms_to_test:
        with console.status(f"[bold blue]Testing {platform_name}..."):
            try:
                service = create_service(platform_name, config)
                if not service:
                    results[platform_name] = "❌ Configuration failed"
                    continue

                # Prepare message and config
                unique_message = make_unique_message(message, config)
                post_config = None

                # Handle Reddit-specific requirements
                if platform_name == "reddit":
                    reddit_config = config.get_platform_config("reddit")
                    subreddit_name = subreddit or reddit_config.get(
                        "default_subreddit", "test"
                    )
                    post_title = (
                        title or f"Test Post - {datetime.now().strftime('%H:%M:%S')}"
                    )

                    reddit_metadata = {"subreddit": subreddit_name, "title": post_title}

                    # Add URL if provided (for link posts)
                    if url:
                        reddit_metadata["url"] = url

                    post_config = PostConfig(metadata=reddit_metadata)

                # Handle different post types
                if threaded and platform_name != "reddit":
                    # Create thread/series
                    thread_messages = [
                        f"{unique_message} - part 1/3",
                        f"{unique_message} - part 2/3",
                        f"{unique_message} - part 3/3",
                    ]

                    if platform_name == "linkedin" and hasattr(service, "post_series"):
                        result = service.post_series(thread_messages)
                    else:
                        result = service.post_thread(thread_messages)

                    results[platform_name] = f"✅ Thread created: {result.thread_url}"
                    created_posts[platform_name] = result.post_results

                else:
                    # Single post
                    post_media = None

                    # Handle media selection
                    if platform_name == "reddit":
                        # Reddit no longer supports media uploads - skip all media
                        post_media = None
                        if media_items:
                            console.print(
                                "[yellow]Warning: Reddit no longer supports media uploads, skipping images[/]"
                            )
                    elif media_items and platform_name != "reddit":
                        post_media = media_items
                    elif document_item and platform_name == "linkedin":
                        post_media = [document_item]

                    result = service.post(
                        unique_message, media=post_media, config=post_config
                    )
                    results[platform_name] = f"✅ Posted: {result.url}"
                    created_posts[platform_name] = [result]

            except Exception as e:
                results[platform_name] = f"❌ Failed: {e}"

    # Display results
    table = Table(title="🚀 Social Media Posting Results")
    table.add_column("Platform", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")

    for platform_name, result in results.items():
        table.add_row(platform_name.title(), result)

    console.print(table)

    # Handle cleanup
    if cleanup and created_posts:
        console.print("\\n[yellow]Cleaning up created posts...[/]")

        for platform_name, posts in created_posts.items():
            try:
                service = create_service(platform_name, config)
                if service:
                    for post in posts:
                        try:
                            service.delete_post(post.post_id)
                            console.print(
                                f"[green]✅ Deleted {platform_name} post: {post.post_id}[/]"
                            )
                        except Exception as e:
                            console.print(
                                f"[red]❌ Failed to delete {platform_name} post: {e}[/]"
                            )
            except Exception as e:
                console.print(f"[red]❌ Cleanup failed for {platform_name}: {e}[/]")


@app.command()
def config_check(
    config_file: Annotated[
        Path, typer.Option("--config", help="Config file path")
    ] = Path("config.json"),
) -> None:
    """Check configuration file validity and show configured platforms."""

    try:
        config = Config(config_file)
    except typer.Exit:
        return

    console.print(Panel.fit("📋 Configuration Check", style="bold blue"))

    # Check platforms
    platforms_table = Table(title="Platform Configuration")
    platforms_table.add_column("Platform", style="cyan")
    platforms_table.add_column("Status", style="green")
    platforms_table.add_column("Details")

    for platform in ["twitter", "bluesky", "linkedin", "reddit"]:
        platform_config = config.get_platform_config(platform)

        if not platform_config:
            platforms_table.add_row(
                platform.title(), "❌ Not configured", "No config found"
            )
        else:
            # Check required fields
            required_fields = {
                "twitter": ["bearer_token"],
                "bluesky": ["handle", "password"],
                "linkedin": ["access_token", "person_urn"],
                "reddit": ["access_token", "user_agent"],
            }

            missing = []
            for field in required_fields[platform]:
                if not platform_config.get(field):
                    missing.append(field)

            if missing:
                platforms_table.add_row(
                    platform.title(), "⚠️ Incomplete", f"Missing: {', '.join(missing)}"
                )
            else:
                platforms_table.add_row(
                    platform.title(), "✅ Configured", "All fields present"
                )

    console.print(platforms_table)

    # Check media files
    console.print("\\n[bold]Media Files:[/]")

    # Images
    single_image = config.get_image_path(1)
    console.print(f"Single image: {'✅ Found' if single_image else '❌ Not found'}")

    multi_images = []
    for i in range(1, 10):  # Check up to 10 images
        img_path = config.get_image_path(i)
        if img_path:
            multi_images.append(f"Image {i}")

    if multi_images:
        console.print(f"Multi images: ✅ {', '.join(multi_images)}")
    else:
        console.print("Multi images: ❌ None found")

    # Documents
    doc_path = config.get_document_path()
    console.print(f"Test document: {'✅ Found' if doc_path else '❌ Not found'}")


@app.command()
def init_config() -> None:
    """Initialize a new config.json file from the example."""

    config_path = Path("config.json")
    example_path = Path("config.example.json")

    if config_path.exists():
        overwrite = typer.confirm(
            f"Config file {config_path} already exists. Overwrite?"
        )
        if not overwrite:
            console.print("[yellow]Config initialization cancelled.[/]")
            raise typer.Exit()

    if not example_path.exists():
        console.print(f"[red]Example config file {example_path} not found![/]")
        raise typer.Exit(1)

    # Copy example to config.json
    import shutil

    shutil.copy2(example_path, config_path)

    console.print(
        Panel.fit(
            f"✅ Created [bold]{config_path}[/] from example\\n"
            "Please edit this file with your API tokens and credentials.",
            style="green",
        )
    )


@app.command()
def examples() -> None:
    """Show detailed usage examples with proper formatting."""

    console.print("\n[bold blue]📚 Social Media CLI Examples[/bold blue]\n")

    # Basic posting examples
    basic_panel = Panel.fit(
        '[dim]$[/dim] [cyan]uv run cli.py post twitter[/cyan] [green]"Hello world!"[/green]\n'
        '[dim]$[/dim] [cyan]uv run cli.py post bluesky[/cyan] [green]"Testing the library"[/green]\n'
        '[dim]$[/dim] [cyan]uv run cli.py post linkedin[/cyan] [green]"Professional update"[/green]',
        title="💬 Text Posts",
        title_align="left",
        border_style="blue",
    )
    console.print(basic_panel)

    # Media examples
    media_panel = Panel.fit(
        '[dim]$[/dim] [cyan]uv run cli.py post bluesky[/cyan] [green]"Check this out"[/green] [yellow]--image=1[/yellow]\n'
        '[dim]$[/dim] [cyan]uv run cli.py post linkedin[/cyan] [green]"Multi-image post"[/green] [yellow]--image=1 --image=2[/yellow]\n'
        '[dim]$[/dim] [cyan]uv run cli.py post linkedin[/cyan] [green]"Document post"[/green] [yellow]--document[/yellow]',
        title="🖼️  With Media",
        title_align="left",
        border_style="green",
    )
    console.print(media_panel)

    # Threading examples
    thread_panel = Panel.fit(
        '[dim]$[/dim] [cyan]uv run cli.py post twitter[/cyan] [green]"Thread test"[/green] [yellow]--threaded[/yellow]\n'
        '[dim]$[/dim] [cyan]uv run cli.py post linkedin[/cyan] [green]"Post series"[/green] [yellow]--threaded[/yellow]',
        title="🧵 Threads",
        title_align="left",
        border_style="magenta",
    )
    console.print(thread_panel)

    # Reddit examples
    reddit_panel = Panel.fit(
        '[dim]$[/dim] [cyan]uv run cli.py post reddit[/cyan] [green]"Text post"[/green] [yellow]--subreddit=test --title="My Title"[/yellow]\n'
        '[dim]$[/dim] [cyan]uv run cli.py post reddit[/cyan] [green]"Link post"[/green] [yellow]--url="https://github.com" --title="GitHub"[/yellow]',
        title="🔗 Reddit",
        title_align="left",
        border_style="red",
    )
    console.print(reddit_panel)

    # Cross-platform and config examples
    util_panel = Panel.fit(
        '[dim]$[/dim] [cyan]uv run cli.py post all[/cyan] [green]"Test all platforms"[/green] [yellow]--cleanup[/yellow]\n'
        "[dim]$[/dim] [cyan]uv run cli.py config-check[/cyan]\n"
        "[dim]$[/dim] [cyan]uv run cli.py init-config[/cyan]",
        title="⚙️  Utilities",
        title_align="left",
        border_style="yellow",
    )
    console.print(util_panel)

    # Footer
    console.print(
        "\n[dim]💡 For detailed documentation, see [bold]dev/README.md[/bold][/dim]\n"
    )


if __name__ == "__main__":
    app()
