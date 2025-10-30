#!/usr/bin/env python3
"""DS1140-PD TUI Prototype

Quick iteration demo showing:
- Button controls for Arm/Fire/Reset
- Input fields for Intensity and Threshold
- Mock moku.set_regs() calls (prints to console)
- Live reload enabled (modify and save to see changes)

Usage:
    uv run python tools/ds1140_tui_prototype.py

    Or with live reload:
    uv run textual run --dev tools/ds1140_tui_prototype.py
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Header, Footer, Input, Label, Static


# ============================================================================
# Voltage Conversion Utilities
# ============================================================================


def voltage_to_digital(voltage: float) -> int:
    """Convert voltage (-5V to +5V) to 16-bit signed integer.

    Args:
        voltage: Voltage value (-5.0 to +5.0)

    Returns:
        16-bit signed integer (−32768 to +32767)
    """
    # Clamp to valid range
    voltage = max(-5.0, min(5.0, voltage))
    return int((voltage / 5.0) * 32767)


def digital_to_voltage(raw_value: int) -> float:
    """Convert 16-bit signed integer to voltage.

    Args:
        raw_value: 16-bit signed integer

    Returns:
        Voltage value (-5.0 to +5.0)
    """
    return (raw_value / 32767.0) * 5.0


# ============================================================================
# Mock Moku Client
# ============================================================================


class MockMoku:
    """Mock Moku device for testing UI without hardware."""

    def __init__(self):
        self.registers = {}

    def set_regs(self, reg_num: int, value: int) -> None:
        """Mock register write (prints to console).

        Args:
            reg_num: Register number (20-28)
            value: 32-bit register value
        """
        self.registers[reg_num] = value
        print(f"[MOKU] set_regs(CR{reg_num}, 0x{value:08X}) = {value}")


# ============================================================================
# DS1140-PD TUI Application
# ============================================================================


class DS1140_TUI(App):
    """DS1140-PD EMFI Probe Control Interface (Prototype)."""

    CSS = """
    Screen {
        background: $surface;
    }

    #title {
        background: $primary;
        color: $text;
        padding: 1;
        text-align: center;
        text-style: bold;
    }

    .section {
        border: solid $primary;
        margin: 1;
        padding: 1;
    }

    .section-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    Button {
        margin: 0 1;
    }

    Input {
        margin: 0 1 1 1;
    }

    .status {
        background: $panel;
        color: $success;
        padding: 1;
        margin: 1;
        text-align: center;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "arm_probe", "Arm Probe"),
        ("f", "force_fire", "Force Fire"),
        ("r", "reset_fsm", "Reset FSM"),
    ]

    def __init__(self):
        super().__init__()
        self.moku = MockMoku()

    def compose(self) -> ComposeResult:
        """Create UI layout."""
        yield Header()

        yield Static("DS1140-PD EMFI Probe Controller", id="title")

        # Control Buttons Section
        with Container(classes="section"):
            yield Label("Control Actions", classes="section-title")
            with Horizontal():
                yield Button("Arm Probe", id="arm", variant="success")
                yield Button("Force Fire", id="fire", variant="error")
                yield Button("Reset FSM", id="reset", variant="primary")

        # Voltage Settings Section
        with Container(classes="section"):
            yield Label("Voltage Settings", classes="section-title")

            yield Label("Intensity (0.0 to 3.0V):")
            yield Input(
                placeholder="Enter voltage (e.g., 2.4)",
                id="intensity",
                value="2.4"
            )

            yield Label("Trigger Threshold (-5.0 to +5.0V):")
            yield Input(
                placeholder="Enter voltage (e.g., 1.5)",
                id="threshold",
                value="1.5"
            )

            with Horizontal():
                yield Button("Set Intensity", id="set_intensity", variant="primary")
                yield Button("Set Threshold", id="set_threshold", variant="primary")

        # Status Display
        yield Static("Ready - No commands sent yet", classes="status", id="status")

        yield Footer()

    # ========================================================================
    # Event Handlers - Easy binding to moku.set_regs()
    # ========================================================================

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle all button presses."""
        button_id = event.button.id

        if button_id == "arm":
            self.action_arm_probe()
        elif button_id == "fire":
            self.action_force_fire()
        elif button_id == "reset":
            self.action_reset_fsm()
        elif button_id == "set_intensity":
            self.set_intensity()
        elif button_id == "set_threshold":
            self.set_threshold()

    # ========================================================================
    # Control Actions
    # ========================================================================

    def action_arm_probe(self) -> None:
        """Send Arm Probe command (CR20, bit 31)."""
        cr20_value = 1 << 31  # Set bit 31
        self.moku.set_regs(20, cr20_value)
        self.update_status("✓ Arm Probe command sent (CR20)")

    def action_force_fire(self) -> None:
        """Send Force Fire command (CR21, bit 31)."""
        cr21_value = 1 << 31
        self.moku.set_regs(21, cr21_value)
        self.update_status("✓ Force Fire command sent (CR21)")

    def action_reset_fsm(self) -> None:
        """Send Reset FSM command (CR22, bit 31)."""
        cr22_value = 1 << 31
        self.moku.set_regs(22, cr22_value)
        self.update_status("✓ Reset FSM command sent (CR22)")

    # ========================================================================
    # Voltage Settings
    # ========================================================================

    def set_intensity(self) -> None:
        """Read Intensity input and send to moku (CR28)."""
        intensity_input = self.query_one("#intensity", Input)

        try:
            voltage = float(intensity_input.value)

            # Validate range (0.0 to 3.0V for DS1140-PD)
            if not 0.0 <= voltage <= 3.0:
                self.update_status(f"✗ Intensity must be 0.0-3.0V (got {voltage}V)")
                return

            # Convert to digital
            raw_value = voltage_to_digital(voltage)

            # Pack into upper 16 bits of CR28
            cr28_value = (raw_value & 0xFFFF) << 16

            # Send to moku
            self.moku.set_regs(28, cr28_value)
            self.update_status(
                f"✓ Intensity set to {voltage}V (raw: 0x{raw_value:04X}, CR28: 0x{cr28_value:08X})"
            )

        except ValueError:
            self.update_status(f"✗ Invalid intensity value: {intensity_input.value}")

    def set_threshold(self) -> None:
        """Read Threshold input and send to moku (CR27)."""
        threshold_input = self.query_one("#threshold", Input)

        try:
            voltage = float(threshold_input.value)

            # Validate range (-5.0 to +5.0V)
            if not -5.0 <= voltage <= 5.0:
                self.update_status(f"✗ Threshold must be -5.0 to +5.0V (got {voltage}V)")
                return

            # Convert to digital
            raw_value = voltage_to_digital(voltage)

            # Pack into upper 16 bits of CR27
            cr27_value = (raw_value & 0xFFFF) << 16

            # Send to moku
            self.moku.set_regs(27, cr27_value)
            self.update_status(
                f"✓ Threshold set to {voltage}V (raw: 0x{raw_value:04X}, CR27: 0x{cr27_value:08X})"
            )

        except ValueError:
            self.update_status(f"✗ Invalid threshold value: {threshold_input.value}")

    # ========================================================================
    # Status Updates
    # ========================================================================

    def update_status(self, message: str) -> None:
        """Update status display."""
        status = self.query_one("#status", Static)
        status.update(message)


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Run the TUI application."""
    app = DS1140_TUI()
    app.run()


if __name__ == "__main__":
    main()
