import click
import logging
from rich.console import Console
from rich.panel import Panel
from envgen.core import EnvFileGenerator

console = Console()

@click.command()
@click.option(
    "--template",
    "-t",
    default=".env.example",
    help="Path to template file (default: .env.example)",
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    default=".env",
    help="Output file path (default: .env)",
    show_default=True,
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing .env file without confirmation",
)
@click.option(
    "--auto-generate",
    "-g",
    is_flag=True,
    help="Auto-generate passwords/secrets for empty sensitive fields",
)
@click.option(
    "--encrypt",
    "-e",
    is_flag=True,
    help="Encrypt .env file using dotenv-vault after generation (requires dotenv-vault CLI)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(template: str, output: str, force: bool, auto_generate: bool, encrypt: bool, verbose: bool):
    """
    🧰 envgen — Generate .env from .env.example interactively.

    Reads a .env.example file in the current directory and prompts you to fill
    missing values to generate a ready-to-use .env file.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    try:
        generator = EnvFileGenerator(
            template_path=template,
            output_path=output,
            auto_generate=auto_generate,
            console=console
        )

        console.print(Panel.fit(
            "[bold green]🧰 envgen v0.2.0 — .env generator with superpowers![/]",
            border_style="blue"
        ))

        env_data = generator.generate_env(force=force)
        generator.write_env_file(env_data)

        if encrypt:
            generator.encrypt_with_dotenv_vault()

        console.print(f"\n✅ [bold green].env file generated at:[/] [cyan]{output}[/]")
        if encrypt:
            console.print("🔐 [bold yellow].env encrypted with dotenv-vault[/]")

    except Exception as e:
        console.print(f"❌ [bold red]Error:[/] {e}", style="red")
        raise click.Abort()


if __name__ == "__main__":
    main()