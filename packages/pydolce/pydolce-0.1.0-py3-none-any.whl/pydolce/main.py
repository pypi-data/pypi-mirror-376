import logging
from typing import Annotated

import rich
import typer

import pydolce
from pydolce.config import DolceConfig

logger = logging.getLogger(__name__)

app = typer.Typer()
_config: DolceConfig = DolceConfig()


@app.command()
def gen() -> None:
    # comming soon
    rich.print("[blue]Coming soon...[/blue]")


@app.command()
def check(
    path: Annotated[
        str,
        typer.Argument(
            help="Path to the Python file or directory to check",
        ),
    ] = ".",
    ignore_missing: Annotated[
        bool | None, typer.Option(help="Ignore functions without docstrings")
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            help="Model name to use (default: codestral for Ollama)",
        ),
    ] = None,
) -> None:
    _config.update(ignore_missing=ignore_missing, model=model)
    rich.print(f"Config:\n{_config.describe()}")
    pydolce.check(
        path=path,
        config=_config,
    )


@app.callback()
def main_callback() -> None:
    version = pydolce.__version__
    rich.print(f"[magenta]Dolce - {version}[/magenta]\n")
    _config = DolceConfig.from_pyproject()


def main() -> None:
    app()
