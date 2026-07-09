from __future__ import annotations

import json

import typer

from jarvis.cli.doctor_checks import run_all_checks, summarize

app = typer.Typer(help="Bootstrap diagnostics for the JARVIS workspace.")


@app.command()
def run(json_output: bool = False) -> None:
    """Run all diagnostics.

    Args:
        json_output: Output JSON results
    """

    results = run_all_checks()
    summary = summarize(results)

    if json_output:
        typer.echo(json.dumps(summary, indent=2))
    else:
        typer.echo("JARVIS Doctor\n==============")
        for result in summary["checks"]:
            status = "✅" if result["passed"] else "❌"
            typer.echo(f"{status} {result['name']}: {result['message']}")
        typer.echo("\nOverall: {}".format("PASS" if summary["passed"] else "FAIL"))

    raise typer.Exit(code=0 if summary["passed"] else 1)


if __name__ == "__main__":
    app()
