"""Database snapshot management CLI commands."""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from jarvis.core.safety.snapshot_manager import SnapshotManager

app = typer.Typer(help="Database snapshot management commands.")
console = Console()


@app.command("create")
def create(name: str = typer.Argument(..., help="Snapshot name")):
    """Create a database snapshot.
    
    Example:
        jarvis snapshot create pre_migration
    """
    manager = SnapshotManager()
    try:
        snapshot = manager.create_snapshot(name)
        console.print(f"[green]✓[/green] Snapshot created: {snapshot.name}")
        console.print(f"  Timestamp: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"  Path: {snapshot.path}")
        console.print(f"  Size: {snapshot.size_bytes / 1024 / 1024:.2f} MB")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create snapshot: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("restore")
def restore(
    name: str = typer.Argument(..., help="Snapshot name"),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation prompt (DANGEROUS - will drop database!)"
    ),
):
    """Restore database from snapshot.
    
    WARNING: This will DROP and recreate the database!
    All data since the snapshot will be lost.
    
    Example:
        jarvis snapshot restore pre_migration --force
    """
    if not force:
        confirm = typer.confirm(
            f"⚠️  WARNING: This will DROP the database and restore from '{name}'. "
            "All data since snapshot will be lost. Continue?",
            abort=True
        )
    
    manager = SnapshotManager()
    try:
        manager.restore_snapshot(name)
        console.print(f"[green]✓[/green] Database restored from snapshot: {name}")
        console.print("  [yellow]Note:[/yellow] You may need to restart services")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to restore snapshot: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("list")
def list_snapshots():
    """List all available snapshots.
    
    Example:
        jarvis snapshot list
    """
    manager = SnapshotManager()
    snapshots = manager.list_snapshots()
    
    if not snapshots:
        console.print("No snapshots found.")
        console.print(f"Snapshot location: {manager.snapshot_dir}")
        return
    
    table = Table(title="Database Snapshots")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Timestamp")
    table.add_column("Size (MB)", justify="right")
    table.add_column("Path", style="dim")
    
    for snapshot in snapshots:
        table.add_row(
            snapshot.name,
            snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            f"{snapshot.size_bytes / 1024 / 1024:.2f}",
            str(snapshot.path.name)
        )
    
    console.print(table)
    console.print(f"\nSnapshot directory: {manager.snapshot_dir}")


@app.command("delete")
def delete(name: str = typer.Argument(..., help="Snapshot name to delete")):
    """Delete a snapshot.
    
    Example:
        jarvis snapshot delete old_backup
    """
    manager = SnapshotManager()
    try:
        manager.delete_snapshot(name)
        console.print(f"[green]✓[/green] Snapshot deleted: {name}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to delete snapshot: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
