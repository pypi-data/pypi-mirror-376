#!/usr/bin/env python3
"""
Universal AWS Profile Management for CloudOps Runbooks Platform

This module provides truly universal AWS profile management that works with ANY AWS setup:
- Single account setups
- Multi-account setups  
- Any profile naming convention
- No specific environment variable requirements

Features:
- Universal compatibility: User --profile → AWS_PROFILE → "default"
- Works with ANY AWS profile names (not just specific test profiles)
- No hardcoded environment variable assumptions
- Simple, reliable profile selection for all users

Author: CloudOps Runbooks Team
Version: 1.0.0 - Universal Compatibility
"""

import os
import time
from typing import Dict, Optional

import boto3

from runbooks.common.rich_utils import console

# Profile cache to reduce duplicate calls (performance optimization)
_profile_cache = {}
_cache_timestamp = None
_cache_ttl = 300  # 5 minutes cache TTL


def get_profile_for_operation(operation_type: str, user_specified_profile: Optional[str] = None) -> str:
    """
    Universal AWS profile selection that works with ANY AWS setup.

    SIMPLE PRIORITY ORDER (Universal Compatibility):
    1. User-specified profile (--profile parameter) - HIGHEST PRIORITY
    2. AWS_PROFILE environment variable - STANDARD AWS CONVENTION
    3. "default" profile - AWS STANDARD FALLBACK

    Works with ANY profile names and ANY AWS setup - no specific environment variable requirements.

    Args:
        operation_type: Type of operation (informational only, not used for profile selection)
        user_specified_profile: Profile specified by user via --profile parameter

    Returns:
        str: Profile name to use for the operation

    Raises:
        SystemExit: If user-specified profile not found in AWS config
    """
    global _profile_cache, _cache_timestamp
    
    # Check cache first to reduce duplicate calls (performance optimization)
    cache_key = f"{operation_type}:{user_specified_profile or 'None'}"
    current_time = time.time()
    
    if (_cache_timestamp and 
        current_time - _cache_timestamp < _cache_ttl and 
        cache_key in _profile_cache):
        return _profile_cache[cache_key]
    
    # Clear cache if TTL expired
    if not _cache_timestamp or current_time - _cache_timestamp >= _cache_ttl:
        _profile_cache.clear()
        _cache_timestamp = current_time
    
    available_profiles = boto3.Session().available_profiles

    # PRIORITY 1: User-specified profile ALWAYS takes precedence
    if user_specified_profile and user_specified_profile != "default":
        if user_specified_profile in available_profiles:
            console.log(f"[green]Using user-specified profile: {user_specified_profile}[/]")
            # Cache the result to reduce duplicate calls
            _profile_cache[cache_key] = user_specified_profile
            return user_specified_profile
        else:
            console.log(f"[red]Error: Profile '{user_specified_profile}' not found in AWS config[/]")
            console.log(f"[yellow]Available profiles: {', '.join(available_profiles)}[/]")
            raise SystemExit(1)

    # PRIORITY 2: AWS_PROFILE environment variable (standard AWS convention)
    aws_profile = os.getenv("AWS_PROFILE")
    if aws_profile and aws_profile in available_profiles:
        console.log(f"[dim cyan]Using AWS_PROFILE environment variable: {aws_profile}[/]")
        # Cache the result to reduce duplicate calls
        _profile_cache[cache_key] = aws_profile
        return aws_profile

    # PRIORITY 3: Default profile (AWS standard fallback)
    default_profile = "default"
    console.log(f"[yellow]Using default AWS profile: {default_profile}[/]")
    # Cache the result to reduce duplicate calls
    _profile_cache[cache_key] = default_profile
    return default_profile


def resolve_profile_for_operation_silent(operation_type: str, user_specified_profile: Optional[str] = None) -> str:
    """
    Universal AWS profile resolution without logging (for display purposes).
    Uses the same universal logic as get_profile_for_operation but without console output.

    Args:
        operation_type: Type of operation (informational only, not used for profile selection)
        user_specified_profile: Profile specified by user via --profile parameter

    Returns:
        str: Profile name to use for the operation

    Raises:
        SystemExit: If user-specified profile not found in AWS config
    """
    available_profiles = boto3.Session().available_profiles

    # PRIORITY 1: User-specified profile ALWAYS takes precedence
    if user_specified_profile and user_specified_profile != "default":
        if user_specified_profile in available_profiles:
            return user_specified_profile
        else:
            # Don't fall back - user explicitly chose this profile
            raise SystemExit(1)

    # PRIORITY 2: AWS_PROFILE environment variable (standard AWS convention)
    aws_profile = os.getenv("AWS_PROFILE")
    if aws_profile and aws_profile in available_profiles:
        return aws_profile

    # PRIORITY 3: Default profile (AWS standard fallback)
    return "default"


def create_cost_session(profile: Optional[str] = None) -> boto3.Session:
    """
    Create a boto3 session for cost operations with universal profile support.
    Works with ANY AWS profile configuration.

    Args:
        profile: User-specified profile (from --profile parameter)

    Returns:
        boto3.Session: Session configured for AWS operations
    """
    selected_profile = get_profile_for_operation("cost", profile)
    return boto3.Session(profile_name=selected_profile)


def create_management_session(profile: Optional[str] = None) -> boto3.Session:
    """
    Create a boto3 session for management operations with universal profile support.
    Works with ANY AWS profile configuration.

    Args:
        profile: User-specified profile (from --profile parameter)

    Returns:
        boto3.Session: Session configured for AWS operations
    """
    selected_profile = get_profile_for_operation("management", profile)
    return boto3.Session(profile_name=selected_profile)


def create_operational_session(profile: Optional[str] = None) -> boto3.Session:
    """
    Create a boto3 session for operational tasks with universal profile support.
    Works with ANY AWS profile configuration.

    Args:
        profile: User-specified profile (from --profile parameter)

    Returns:
        boto3.Session: Session configured for AWS operations
    """
    selected_profile = get_profile_for_operation("operational", profile)
    return boto3.Session(profile_name=selected_profile)


def get_current_profile_info() -> Dict[str, Optional[str]]:
    """
    Get current AWS profile information using universal approach.
    Works with ANY AWS setup without hardcoded environment variable assumptions.

    Returns:
        Dict with current profile information
    """
    return {
        "aws_profile": os.getenv("AWS_PROFILE"),
        "default_profile": "default",
        "available_profiles": boto3.Session().available_profiles
    }


def validate_profile_access(profile_name: str, operation_type: str = "general") -> bool:
    """
    Validate that profile exists and is accessible.

    Args:
        profile_name: AWS profile name to validate
        operation_type: Type of operation for context

    Returns:
        bool: True if profile is valid and accessible
    """
    try:
        available_profiles = boto3.Session().available_profiles
        if profile_name not in available_profiles:
            console.log(f"[red]Profile '{profile_name}' not found in AWS config[/]")
            return False

        # Test session creation
        session = boto3.Session(profile_name=profile_name)
        sts_client = session.client("sts")
        identity = sts_client.get_caller_identity()

        console.log(f"[green]Profile '{profile_name}' validated for {operation_type} operations[/]")
        console.log(f"[dim]Account: {identity.get('Account')}, User: {identity.get('UserId', 'Unknown')}[/]")
        return True

    except Exception as e:
        console.log(f"[red]Profile '{profile_name}' validation failed: {str(e)}[/]")
        return False


def get_available_profiles_for_validation() -> list:
    """
    Get available AWS profiles for validation - truly universal approach.
    
    Returns all configured AWS profiles for validation without ANY hardcoded assumptions.
    Works with any AWS setup: single account, multi-account, any profile naming convention.
    
    Returns:
        list: Available AWS profile names for validation
    """
    try:
        # Get all available profiles from AWS CLI configuration
        available_profiles = boto3.Session().available_profiles
        
        # Start with AWS_PROFILE if set
        validation_profiles = []
        aws_profile = os.getenv("AWS_PROFILE")
        if aws_profile and aws_profile in available_profiles:
            validation_profiles.append(aws_profile)
        
        # Add all other available profiles (universal approach)
        for profile in available_profiles:
            if profile not in validation_profiles:
                validation_profiles.append(profile)
        
        # Ensure we have at least one profile to test
        if not validation_profiles:
            validation_profiles = ['default']
            
        return validation_profiles
        
    except Exception as e:
        console.log(f"[yellow]Warning: Could not detect AWS profiles: {e}[/]")
        return ['default']  # Fallback to default profile


# Export all public functions
__all__ = [
    "get_profile_for_operation",
    "resolve_profile_for_operation_silent",
    "create_cost_session", 
    "create_management_session",
    "create_operational_session",
    "get_current_profile_info",
    "validate_profile_access",
    "get_available_profiles_for_validation",
]
