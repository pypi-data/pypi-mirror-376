"""
FinOps Scenario CLI Integration - Phase 1 Priority 2

This module provides CLI integration for the Business Scenario Matrix with intelligent
parameter defaults and scenario-specific help generation.

Strategic Achievement: Manager requires business scenario intelligence with smart
parameter recommendations per business case type.
"""

import click
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .business_case_config import (
    get_business_case_config,
    get_business_scenario_matrix,
    BusinessScenarioMatrix,
    ScenarioParameter
)
from ..common.rich_utils import print_header, print_info, print_success, print_warning


class ScenarioCliHelper:
    """
    CLI integration helper for business scenario intelligence.

    Provides intelligent parameter recommendations and scenario-specific help.
    """

    def __init__(self):
        """Initialize CLI helper with scenario matrix."""
        self.console = Console()
        self.business_config = get_business_case_config()
        self.scenario_matrix = get_business_scenario_matrix()

    def display_scenario_help(self, scenario_key: Optional[str] = None) -> None:
        """Display scenario-specific help with parameter recommendations."""
        print_header("FinOps Business Scenarios", "Parameter Intelligence")

        if scenario_key:
            self._display_single_scenario_help(scenario_key)
        else:
            self._display_all_scenarios_help()

    def _display_single_scenario_help(self, scenario_key: str) -> None:
        """Display detailed help for a single scenario."""
        scenario_config = self.business_config.get_scenario(scenario_key)
        if not scenario_config:
            print_warning(f"Unknown scenario: {scenario_key}")
            return

        # Display scenario overview
        self.console.print(f"\n[bold cyan]Scenario: {scenario_config.display_name}[/bold cyan]")
        self.console.print(f"[dim]Business Case: {scenario_config.business_description}[/dim]")
        self.console.print(f"[dim]Technical Focus: {scenario_config.technical_focus}[/dim]")
        self.console.print(f"[dim]Savings Target: {scenario_config.savings_range_display}[/dim]")
        self.console.print(f"[dim]Risk Level: {scenario_config.risk_level}[/dim]")

        # Display parameter recommendations
        recommendations = self.scenario_matrix.get_parameter_recommendations(scenario_key)
        if recommendations:
            self.console.print(f"\n[bold green]🎯 Intelligent Parameter Recommendations[/bold green]")

            for param_key, param in recommendations.items():
                self._display_parameter_recommendation(param)

            # Display optimal command
            optimal_command = self._generate_optimal_command(scenario_key, recommendations)
            self.console.print(f"\n[bold yellow]💡 Optimal Command Example:[/bold yellow]")
            self.console.print(f"[dim]runbooks finops --scenario {scenario_key} {optimal_command}[/dim]")
        else:
            print_info("Using standard parameters for this scenario")

    def _display_all_scenarios_help(self) -> None:
        """Display overview of all scenarios with parameter summaries."""
        # Create scenarios overview table
        table = Table(
            title="🎯 Business Scenarios with Intelligent Parameter Defaults",
            show_header=True,
            header_style="bold cyan"
        )

        table.add_column("Scenario", style="bold white", width=15)
        table.add_column("Business Case", style="cyan", width=25)
        table.add_column("Savings Target", style="green", width=15)
        table.add_column("Optimal Parameters", style="yellow", width=35)
        table.add_column("Tier", style="magenta", width=8)

        # Get scenario summaries
        scenario_summaries = self.scenario_matrix.get_all_scenario_summaries()

        # Tier classification for display
        tier_mapping = {
            'workspaces': 'Tier 1',
            'nat-gateway': 'Tier 1',
            'rds-snapshots': 'Tier 1',
            'ebs-optimization': 'Tier 2',
            'vpc-cleanup': 'Tier 2',
            'elastic-ip': 'Tier 2',
            'backup-investigation': 'Tier 3'
        }

        for scenario_key, scenario in self.business_config.get_all_scenarios().items():
            parameter_summary = scenario_summaries.get(scenario_key, "Standard")
            tier = tier_mapping.get(scenario_key, "Standard")

            table.add_row(
                scenario_key,
                scenario.display_name,
                scenario.savings_range_display,
                parameter_summary,
                tier
            )

        self.console.print(table)

        # Display usage instructions
        usage_panel = Panel(
            """[bold]Usage Examples:[/bold]

[cyan]Tier 1 High-Value Scenarios:[/cyan]
• runbooks finops --scenario workspaces --time-range 90 --pdf
• runbooks finops --scenario nat-gateway --time-range 30 --json --amortized
• runbooks finops --scenario rds-snapshots --time-range 90 --csv --dual-metrics

[cyan]Tier 2 Strategic Scenarios:[/cyan]
• runbooks finops --scenario ebs-optimization --time-range 180 --pdf --dual-metrics
• runbooks finops --scenario vpc-cleanup --time-range 30 --csv --unblended
• runbooks finops --scenario elastic-ip --time-range 7 --json --unblended

[cyan]Get Scenario-Specific Help:[/cyan]
• runbooks finops --scenario workspaces --help-scenario
• runbooks finops --help-scenarios  # All scenarios overview
            """,
            title="📚 Scenario Usage Guide",
            style="cyan"
        )
        self.console.print(usage_panel)

    def _display_parameter_recommendation(self, param: ScenarioParameter) -> None:
        """Display a single parameter recommendation."""
        # Format parameter display
        if isinstance(param.optimal_value, bool) and param.optimal_value:
            param_display = f"[bold]{param.name}[/bold]"
        else:
            param_display = f"[bold]{param.name} {param.optimal_value}[/bold]"

        self.console.print(f"  {param_display}")
        self.console.print(f"    [dim]→ {param.business_justification}[/dim]")

        if param.alternative_values:
            alternatives = ', '.join(str(v) for v in param.alternative_values)
            self.console.print(f"    [dim]Alternatives: {alternatives}[/dim]")
        self.console.print()

    def _generate_optimal_command(self, scenario_key: str, recommendations: Dict[str, ScenarioParameter]) -> str:
        """Generate optimal command example from recommendations."""
        command_parts = []

        for param_key, param in recommendations.items():
            if isinstance(param.optimal_value, bool) and param.optimal_value:
                command_parts.append(param.name)
            else:
                command_parts.append(f"{param.name} {param.optimal_value}")

        return " ".join(command_parts)

    def validate_scenario_parameters(self, scenario_key: str, provided_params: Dict[str, Any]) -> None:
        """Validate and provide suggestions for scenario parameters."""
        suggestions = self.scenario_matrix.validate_parameters_for_scenario(scenario_key, provided_params)

        if suggestions:
            self.console.print(f"\n[bold yellow]💡 Parameter Optimization Suggestions for '{scenario_key}':[/bold yellow]")
            for param_type, suggestion in suggestions.items():
                self.console.print(f"  [yellow]→[/yellow] {suggestion}")
            self.console.print()

    def get_scenario_cli_choices(self) -> List[str]:
        """Get list of valid scenario choices for Click options."""
        return self.business_config.get_scenario_choices()

    def get_enhanced_scenario_help_text(self) -> str:
        """Get enhanced help text including parameter intelligence."""
        base_help = self.business_config.get_scenario_help_text()
        return f"{base_help}\n\nUse --scenario [scenario-name] for specific optimization analysis."


def display_scenario_matrix_help(scenario_key: Optional[str] = None) -> None:
    """
    Display business scenario matrix help with parameter intelligence.

    Args:
        scenario_key: Specific scenario to show help for, or None for all scenarios
    """
    helper = ScenarioCliHelper()
    helper.display_scenario_help(scenario_key)


def validate_and_suggest_parameters(scenario_key: str, cli_params: Dict[str, Any]) -> None:
    """
    Validate CLI parameters against scenario recommendations and provide suggestions.

    Args:
        scenario_key: The business scenario being executed
        cli_params: Dictionary of provided CLI parameters
    """
    helper = ScenarioCliHelper()
    helper.validate_scenario_parameters(scenario_key, cli_params)


def get_scenario_parameter_defaults(scenario_key: str) -> Dict[str, Any]:
    """
    Get parameter defaults for a specific scenario.

    Args:
        scenario_key: The business scenario key

    Returns:
        Dictionary of parameter defaults that can be applied to CLI arguments
    """
    matrix = get_business_scenario_matrix()
    recommendations = matrix.get_parameter_recommendations(scenario_key)

    defaults = {}

    for param_key, param in recommendations.items():
        if param.name == '--time-range':
            defaults['time_range'] = param.optimal_value
        elif param.name == '--unblended':
            defaults['unblended'] = True
        elif param.name == '--amortized':
            defaults['amortized'] = True
        elif param.name == '--dual-metrics':
            defaults['dual_metrics'] = True
        elif param.name == '--pdf':
            defaults['pdf'] = True
        elif param.name == '--csv':
            defaults['csv'] = True
        elif param.name == '--json':
            defaults['json'] = True
        elif param.name == '--markdown':
            defaults['export_markdown'] = True

    return defaults