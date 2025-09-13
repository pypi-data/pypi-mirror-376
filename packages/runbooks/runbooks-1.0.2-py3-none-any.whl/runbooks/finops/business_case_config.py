"""
Dynamic Business Case Configuration - Enterprise Template System

Strategic Achievement: Replace hardcoded JIRA references with dynamic business case templates
- Enterprise naming conventions with configurable business scenarios
- Dynamic financial targets and achievement tracking
- Reusable template system for unlimited business case scaling

This module provides configurable business case templates following enterprise standards:
- "Do one thing and do it well": Centralized configuration management
- "Move Fast, But Not So Fast We Crash": Proven template patterns with validation
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class BusinessCaseType(Enum):
    """Standard business case types for enterprise scenarios."""
    COST_OPTIMIZATION = "cost_optimization"
    RESOURCE_CLEANUP = "resource_cleanup"
    COMPLIANCE_FRAMEWORK = "compliance_framework"
    SECURITY_ENHANCEMENT = "security_enhancement"
    AUTOMATION_DEPLOYMENT = "automation_deployment"


@dataclass
class BusinessScenario:
    """Dynamic business scenario configuration."""
    scenario_id: str
    display_name: str
    business_case_type: BusinessCaseType
    target_savings_min: Optional[float] = None
    target_savings_max: Optional[float] = None
    business_description: str = ""
    technical_focus: str = ""
    risk_level: str = "Medium"
    implementation_status: str = "Analysis"
    cli_command_suffix: str = ""
    
    @property
    def scenario_display_id(self) -> str:
        """Generate enterprise-friendly scenario display ID."""
        return f"{self.business_case_type.value.replace('_', '-').title()}-{self.scenario_id}"
    
    @property
    def savings_range_display(self) -> str:
        """Generate savings range display for business presentations."""
        if self.target_savings_min and self.target_savings_max:
            if self.target_savings_min == self.target_savings_max:
                return f"${self.target_savings_min:,.0f}/year"
            else:
                return f"${self.target_savings_min:,.0f}-${self.target_savings_max:,.0f}/year"
        elif self.target_savings_min:
            return f"${self.target_savings_min:,.0f}+/year"
        else:
            return "Analysis pending"


class BusinessCaseConfigManager:
    """Enterprise business case configuration manager."""
    
    def __init__(self, config_source: Optional[str] = None):
        """
        Initialize business case configuration manager.
        
        Args:
            config_source: Optional path to configuration file or environment variable prefix
        """
        self.config_source = config_source or "RUNBOOKS_BUSINESS_CASE"
        self.scenarios = self._load_default_scenarios()
        self._load_environment_overrides()
    
    def _load_default_scenarios(self) -> Dict[str, BusinessScenario]:
        """Load default enterprise business scenarios."""
        return {
            "workspaces": BusinessScenario(
                scenario_id="workspaces",
                display_name="WorkSpaces Resource Optimization",
                business_case_type=BusinessCaseType.RESOURCE_CLEANUP,
                target_savings_min=12000,
                target_savings_max=15000,
                business_description="Identify and optimize unused Amazon WorkSpaces for cost efficiency",
                technical_focus="Zero-usage WorkSpaces detection and cost analysis",
                risk_level="Low",
                cli_command_suffix="workspaces"
            ),
            "rds-snapshots": BusinessScenario(
                scenario_id="rds-snapshots", 
                display_name="RDS Storage Optimization",
                business_case_type=BusinessCaseType.RESOURCE_CLEANUP,
                target_savings_min=5000,
                target_savings_max=24000,
                business_description="Optimize manual RDS snapshots to reduce storage costs",
                technical_focus="Manual RDS snapshot lifecycle management",
                risk_level="Medium",
                cli_command_suffix="snapshots"
            ),
            "backup-investigation": BusinessScenario(
                scenario_id="backup-investigation",
                display_name="Backup Infrastructure Analysis", 
                business_case_type=BusinessCaseType.COMPLIANCE_FRAMEWORK,
                business_description="Investigate backup account utilization and optimization opportunities",
                technical_focus="Backup infrastructure resource utilization analysis",
                risk_level="Medium",
                implementation_status="Framework",
                cli_command_suffix="commvault"
            ),
            "nat-gateway": BusinessScenario(
                scenario_id="nat-gateway",
                display_name="Network Gateway Optimization",
                business_case_type=BusinessCaseType.COST_OPTIMIZATION,
                target_savings_min=8000,
                target_savings_max=12000,
                business_description="Optimize NAT Gateway configurations for cost efficiency",
                technical_focus="NAT Gateway usage analysis and rightsizing",
                cli_command_suffix="nat-gateway"
            ),
            "elastic-ip": BusinessScenario(
                scenario_id="elastic-ip",
                display_name="IP Address Resource Management",
                business_case_type=BusinessCaseType.RESOURCE_CLEANUP,
                target_savings_min=44,  # $3.65 * 12 months
                business_description="Optimize unattached Elastic IP addresses",
                technical_focus="Elastic IP attachment analysis and cleanup recommendations",
                risk_level="Low",
                cli_command_suffix="elastic-ip"
            ),
            "ebs-optimization": BusinessScenario(
                scenario_id="ebs-optimization",
                display_name="Storage Volume Optimization",
                business_case_type=BusinessCaseType.COST_OPTIMIZATION,
                business_description="Optimize EBS volume types and utilization for cost efficiency",
                technical_focus="EBS volume rightsizing and type optimization (15-20% potential)",
                cli_command_suffix="ebs"
            ),
            "vpc-cleanup": BusinessScenario(
                scenario_id="vpc-cleanup",
                display_name="Network Infrastructure Cleanup",
                business_case_type=BusinessCaseType.RESOURCE_CLEANUP,
                target_savings_min=5869,
                business_description="Clean up unused VPC resources and infrastructure",
                technical_focus="VPC resource utilization analysis and cleanup recommendations",
                cli_command_suffix="vpc-cleanup"
            )
        }
    
    def _load_environment_overrides(self) -> None:
        """Load configuration overrides from environment variables."""
        prefix = f"{self.config_source}_"
        
        for scenario_key, scenario in self.scenarios.items():
            # Check for scenario-specific overrides
            env_key = f"{prefix}{scenario_key.upper().replace('-', '_')}"
            
            # Override target savings if specified
            min_savings = os.getenv(f"{env_key}_MIN_SAVINGS")
            max_savings = os.getenv(f"{env_key}_MAX_SAVINGS")
            
            if min_savings:
                scenario.target_savings_min = float(min_savings)
            if max_savings:
                scenario.target_savings_max = float(max_savings)
                
            # Override display name if specified
            display_name = os.getenv(f"{env_key}_DISPLAY_NAME")
            if display_name:
                scenario.display_name = display_name
                
            # Override business description if specified  
            description = os.getenv(f"{env_key}_DESCRIPTION")
            if description:
                scenario.business_description = description
    
    def get_scenario(self, scenario_key: str) -> Optional[BusinessScenario]:
        """Get business scenario by key."""
        return self.scenarios.get(scenario_key)
    
    def get_all_scenarios(self) -> Dict[str, BusinessScenario]:
        """Get all configured business scenarios."""
        return self.scenarios
    
    def get_scenario_choices(self) -> List[str]:
        """Get list of valid scenario keys for CLI choice options."""
        return list(self.scenarios.keys())
    
    def get_scenario_help_text(self) -> str:
        """Generate help text for CLI scenario option."""
        help_parts = []
        for key, scenario in self.scenarios.items():
            savings_display = scenario.savings_range_display
            help_parts.append(f"{key} ({scenario.display_name}: {savings_display})")
        return "Business scenario analysis: " + ", ".join(help_parts)
    
    def format_scenario_for_display(self, scenario_key: str, 
                                  achieved_savings: Optional[float] = None,
                                  achievement_percentage: Optional[float] = None) -> str:
        """Format scenario for display in tables and reports."""
        scenario = self.get_scenario(scenario_key)
        if not scenario:
            return f"Unknown scenario: {scenario_key}"
        
        base_info = f"{scenario.display_name} ({scenario.savings_range_display})"
        
        if achieved_savings:
            base_info += f" - Achieved: ${achieved_savings:,.0f}"
            
        if achievement_percentage:
            base_info += f" ({achievement_percentage:.0f}% of target)"
            
        return base_info
    
    def create_business_case_summary(self) -> Dict[str, Any]:
        """Create executive summary of all business cases."""
        total_min_savings = sum(
            scenario.target_savings_min or 0 
            for scenario in self.scenarios.values()
        )
        
        total_max_savings = sum(
            scenario.target_savings_max or 0 
            for scenario in self.scenarios.values() 
            if scenario.target_savings_max
        )
        
        return {
            "total_scenarios": len(self.scenarios),
            "total_potential_min": total_min_savings,
            "total_potential_max": total_max_savings,
            "potential_range": f"${total_min_savings:,.0f}-${total_max_savings:,.0f}",
            "scenarios_by_type": {
                case_type.value: [
                    s.display_name for s in self.scenarios.values() 
                    if s.business_case_type == case_type
                ]
                for case_type in BusinessCaseType
            }
        }


# Global configuration manager instance
_config_manager = None

def get_business_case_config() -> BusinessCaseConfigManager:
    """Get global business case configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = BusinessCaseConfigManager()
    return _config_manager


def get_scenario_display_name(scenario_key: str) -> str:
    """Get enterprise-friendly display name for scenario."""
    config = get_business_case_config()
    scenario = config.get_scenario(scenario_key)
    return scenario.display_name if scenario else scenario_key.title()


def get_scenario_savings_range(scenario_key: str) -> str:
    """Get savings range display for scenario."""
    config = get_business_case_config()
    scenario = config.get_scenario(scenario_key)
    return scenario.savings_range_display if scenario else "Analysis pending"


def format_business_achievement(scenario_key: str, achieved_savings: float) -> str:
    """Format business achievement for executive reporting."""
    config = get_business_case_config()
    scenario = config.get_scenario(scenario_key)
    
    if not scenario:
        return f"{scenario_key}: ${achieved_savings:,.0f} annual savings"
    
    # Calculate achievement percentage if target is available
    achievement_text = f"{scenario.display_name}: ${achieved_savings:,.0f} annual savings"
    
    if scenario.target_savings_min:
        percentage = (achieved_savings / scenario.target_savings_min) * 100
        achievement_text += f" ({percentage:.0f}% of target)"
    
    return achievement_text


# Migration helper functions for existing hardcoded patterns
def migrate_legacy_scenario_reference(legacy_ref: str) -> str:
    """
    Migrate legacy JIRA references to dynamic business case keys.
    
    Args:
        legacy_ref: Legacy reference like "FinOps-24", "finops-23", etc.
    
    Returns:
        Dynamic business case key
    """
    legacy_mapping = {
        "finops-24": "workspaces",
        "FinOps-24": "workspaces", 
        "finops-23": "rds-snapshots",
        "FinOps-23": "rds-snapshots",
        "finops-25": "backup-investigation",
        "FinOps-25": "backup-investigation",
        "finops-26": "nat-gateway",
        "FinOps-26": "nat-gateway",
        "finops-eip": "elastic-ip",
        "FinOps-EIP": "elastic-ip",
        "finops-ebs": "ebs-optimization",
        "FinOps-EBS": "ebs-optimization",
        "awso-05": "vpc-cleanup",
        "AWSO-05": "vpc-cleanup"
    }
    
    return legacy_mapping.get(legacy_ref, legacy_ref.lower())