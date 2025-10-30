#!/usr/bin/env python3
"""
CustomInstApp Code Generator

Generates VHDL shim and main template files from CustomInstApp YAML definition.

Usage:
    python tools/generate_custom_inst.py \\
        --config modules/PulseStar/PulseStar_app.yaml \\
        --output modules/PulseStar/custom_inst_main/

Generated Files:
    - <AppName>_custom_inst_shim.vhd  (ALWAYS regenerated)
    - <AppName>_custom_inst_main.vhd  (ONLY if doesn't exist)

Design Pattern:
    The shim layer is 100% GENERATED from the Pydantic model.
    NEVER hand-edit the shim - always regenerate from YAML.
    The main layer is a template for developers to implement app logic.

References:
    - docs/VOLO_APP_DESIGN.md
    - docs/VOLO_APP_FRESH_CONTEXT.md
"""

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.custom_inst import CustomInstApp


def print_banner():
    """Print tool banner."""
    console = Console()
    console.print(Panel.fit(
        "[bold cyan]CustomInstApp Code Generator[/bold cyan]\n"
        "Generate VHDL shim and main template from CustomInstApp definition",
        border_style="cyan"
    ))


def print_register_table(app: CustomInstApp):
    """Print register mapping table."""
    console = Console()

    table = Table(title=f"[bold]{app.name}[/bold] Register Mapping", show_header=True)
    table.add_column("CR", style="cyan", justify="center")
    table.add_column("Register Name", style="green")
    table.add_column("Signal Name", style="yellow")
    table.add_column("Type", style="magenta")

    for reg in app.registers:
        signal_name = app.to_vhdl_signal_name(reg.name)
        vhdl_type = app.get_vhdl_type_declaration(reg)
        table.add_row(
            f"CR{reg.cr_number}",
            reg.name,
            signal_name,
            vhdl_type
        )

    console.print(table)


def print_summary(shim_path: Path, main_path: Path, main_created: bool):
    """Print generation summary."""
    console = Console()

    console.print("\n[bold green]✓ Generation Complete![/bold green]\n")

    console.print("[bold]Generated Files:[/bold]")
    console.print(f"  [cyan]→[/cyan] {shim_path} [yellow](GENERATED - do not edit)[/yellow]")

    if main_created:
        console.print(f"  [cyan]→[/cyan] {main_path} [green](TEMPLATE - implement app logic)[/green]")
    else:
        console.print(f"  [cyan]→[/cyan] {main_path} [blue](SKIPPED - already exists)[/blue]")

    console.print("\n[bold]Next Steps:[/bold]")
    console.print("  1. Implement application logic in [green]<AppName>_custom_inst_main.vhd[/green]")
    console.print("  2. Build MCC package: [cyan]uv run python scripts/build_mcc_package.py <module>[/cyan]")
    console.print("  3. Upload to CloudCompile and download results")
    console.print("  4. Deploy with: [cyan]python tools/custom_inst_loader.py --config <yaml> --device <name> --ip <ip>[/cyan]")


def generate_custom_inst(config_path: Path, output_dir: Path, force: bool = False):
    """
    Generate CustomInstApp VHDL files.

    Args:
        config_path: Path to CustomInstApp YAML definition
        output_dir: Output directory for generated files
        force: If True, overwrite existing main template
    """
    console = Console()

    # Load CustomInstApp from YAML
    console.print(f"\n[cyan]→[/cyan] Loading CustomInstApp from {config_path}")
    try:
        app = CustomInstApp.load_from_yaml(config_path)
    except Exception as e:
        console.print(f"[red]✗ Error loading YAML:[/red] {e}")
        sys.exit(1)

    console.print(f"[green]✓[/green] Loaded {app.name} v{app.version}")
    console.print(f"  Registers: {len(app.registers)}")
    console.print(f"  Bitstream: {app.bitstream_path}")
    if app.buffer_path:
        console.print(f"  Buffer: {app.buffer_path}")

    # Print register mapping
    print_register_table(app)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Template paths
    project_root = Path(__file__).parent.parent
    shim_template_path = project_root / "shared" / "volo" / "templates" / "custom_inst_shim_template.vhd"
    main_template_path = project_root / "shared" / "volo" / "templates" / "custom_inst_main_template.vhd"

    # Output paths
    shim_output_path = output_dir / f"{app.name}_custom_inst_shim.vhd"
    main_output_path = output_dir / f"{app.name}_custom_inst_main.vhd"

    # Generate shim (ALWAYS)
    console.print(f"\n[cyan]→[/cyan] Generating shim layer...")
    try:
        shim_vhdl = app.generate_vhdl_shim(shim_template_path)
        with open(shim_output_path, 'w') as f:
            f.write(shim_vhdl)
        console.print(f"[green]✓[/green] Generated {shim_output_path}")
    except Exception as e:
        console.print(f"[red]✗ Error generating shim:[/red] {e}")
        sys.exit(1)

    # Generate main template (ONLY if doesn't exist or force=True)
    main_created = False
    if not main_output_path.exists() or force:
        console.print(f"\n[cyan]→[/cyan] Generating main template...")
        try:
            main_vhdl = app.generate_vhdl_main_template(main_template_path)
            with open(main_output_path, 'w') as f:
                f.write(main_vhdl)
            console.print(f"[green]✓[/green] Generated {main_output_path}")
            main_created = True
        except Exception as e:
            console.print(f"[red]✗ Error generating main template:[/red] {e}")
            sys.exit(1)
    else:
        console.print(f"\n[blue]→[/blue] Skipping main template (already exists)")
        console.print(f"  Use --force to overwrite: {main_output_path}")

    # Print summary
    print_summary(shim_output_path, main_output_path, main_created)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate CustomInstApp VHDL files from YAML definition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate PulseStar volo-app files
  python tools/generate_custom_inst.py \\
      --config modules/PulseStar/PulseStar_app.yaml \\
      --output modules/PulseStar/custom_inst_main/

  # Force regenerate main template (WARNING: overwrites existing)
  python tools/generate_custom_inst.py \\
      --config modules/MyApp/MyApp_app.yaml \\
      --output modules/MyApp/custom_inst_main/ \\
      --force

References:
  - docs/VOLO_APP_DESIGN.md - Complete architecture
  - docs/VOLO_APP_FRESH_CONTEXT.md - Quick start guide
        """
    )

    parser.add_argument(
        '--config',
        type=Path,
        required=True,
        help='Path to CustomInstApp YAML definition (e.g., PulseStar_app.yaml)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output directory for generated files (e.g., modules/PulseStar/custom_inst_main/)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force overwrite existing main template (WARNING: destroys edits!)'
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)

    # Print banner
    print_banner()

    # Generate files
    generate_custom_inst(args.config, args.output, args.force)


if __name__ == '__main__':
    main()
