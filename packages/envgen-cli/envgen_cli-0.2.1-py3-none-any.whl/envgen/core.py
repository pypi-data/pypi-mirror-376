import os
import secrets
import string
import subprocess
import logging
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger(__name__)


class DummyConsole:
    """Fallback console for environments without rich."""
    def print(self, *args: Any, **kwargs: Any) -> None:
        print(*args)

    def input(self, prompt: str) -> str:
        return input(prompt)


class EnvFileGenerator:
    """
    Core logic for parsing .env.example and generating .env interactively.
    """

    def __init__(
        self,
        template_path: str = ".env.example",
        output_path: str = ".env",
        auto_generate: bool = False,
        console: Optional[Any] = None
    ):
        self.template_path = template_path
        self.output_path = output_path
        self.auto_generate = auto_generate
        self.console = console or DummyConsole()

    def parse_template(self) -> List[Tuple[str, Optional[str]]]:
        """Parse .env.example into list of (key, default_value) pairs."""
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template file not found: {self.template_path}")

        entries: List[Tuple[str, Optional[str]]] = []
        with open(self.template_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if "=" not in line:
                    logger.warning(f"Line {line_num}: Invalid format (no '='): {line}")
                    continue

                key, *rest = line.split("=", 1)
                key = key.strip()
                value = rest[0].strip() if rest else ""

                if not key:
                    logger.warning(f"Line {line_num}: Empty key: {line}")
                    continue

                entries.append((key, value if value else None))

        return entries

    def generate_password(self, length: int = 32) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def prompt_user(self, key: str, default: Optional[str] = None) -> str:
        """Prompt user for value. Auto-generate if enabled and field is sensitive."""
        is_sensitive = any(x in key.upper() for x in ["KEY", "PASS", "SECRET", "TOKEN", "JWT"])

        prompt_text = f"{key}"
        if default:
            prompt_text += f" [default: {default}]"

        # Auto-generate for sensitive fields if enabled
        if is_sensitive and self.auto_generate and not default:
            generated = self.generate_password()
            if hasattr(self.console, 'input'):
                # We'll handle rich.prompt inside this block only if needed
                from rich.prompt import Confirm
                accept = Confirm.ask(
                    f"{prompt_text}\n[bold yellow]Auto-generated:[/] [cyan]{generated}[/]\nUse this value?",
                    default=True,
                    console=self.console
                )
                if accept:
                    return generated
            else:
                print(f"Auto-generated for {key}: {generated}")
                use = input("Use this value? (Y/n): ").strip().lower()
                if use in ("", "y", "yes"):
                    return generated

        # Otherwise, prompt normally
        while True:
            try:
                if is_sensitive and not hasattr(self.console, 'input'):
                    import getpass
                    value = getpass.getpass(f"{prompt_text}: ")
                else:
                    if hasattr(self.console, 'input'):
                        from rich.prompt import Prompt
                        value = Prompt.ask(prompt_text, password=is_sensitive, console=self.console)
                    else:
                        value = self.console.input(f"{prompt_text}: ")

            except KeyboardInterrupt:
                print("\nAborted by user.")
                exit(1)

            if value:
                return value
            elif default is not None:
                return default
            else:
                if hasattr(self.console, 'print'):
                    self.console.print("[red]Value required. Please enter a value.[/]")
                else:
                    print("Value required. Please enter a value.")

    def generate_env(self, force: bool = False) -> Dict[str, str]:
        """Generate .env file by prompting user for missing values."""
        if os.path.exists(self.output_path) and not force:
            raise FileExistsError(
                f"Output file '{self.output_path}' exists. Use --force to overwrite."
            )

        entries = self.parse_template()
        result: Dict[str, str] = {}

        if hasattr(self.console, 'print'):
            self.console.print("[bold blue]Generating .env file...[/]")
            self.console.print("[dim]" + "-" * 40 + "[/]")

        for key, default in entries:
            value = self.prompt_user(key, default)
            result[key] = value

        if hasattr(self.console, 'print'):
            self.console.print("[dim]" + "-" * 40 + "[/]")

        return result

    def write_env_file(self, data: Dict[str, str]) -> None:
        """Write key-value pairs to .env file."""
        with open(self.output_path, "w", encoding="utf-8") as f:
            for key, value in data.items():
                f.write(f"{key}={value}\n")

    def encrypt_with_dotenv_vault(self) -> None:
        """Encrypt .env file using dotenv-vault CLI — graceful fallback if not installed."""
        try:
            result = subprocess.run(
                ["dotenv-vault", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise FileNotFoundError("dotenv-vault CLI not found. Install it via: npm install -g dotenv-vault")

            result = subprocess.run(
                ["dotenv-vault", "build"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"dotenv-vault failed: {result.stderr}")

            if hasattr(self.console, 'print'):
                self.console.print("[green]🔒 .env encrypted successfully with dotenv-vault.[/]")

        except FileNotFoundError as e:
            if hasattr(self.console, 'print'):
                self.console.print(f"[red]🔐 dotenv-vault not found:[/] {e}")
                self.console.print("[yellow]💡 Tip:[/] Install it via: [bold]npm install -g dotenv-vault[/]")
            else:
                print(f"🔐 dotenv-vault not found: {e}")
                print("💡 Tip: Install it via: npm install -g dotenv-vault")
            raise
        except Exception as e:
            if hasattr(self.console, 'print'):
                self.console.print(f"[red]🔐 Failed to encrypt with dotenv-vault:[/] {e}")
            else:
                print(f"🔐 Failed to encrypt with dotenv-vault: {e}")
            raise