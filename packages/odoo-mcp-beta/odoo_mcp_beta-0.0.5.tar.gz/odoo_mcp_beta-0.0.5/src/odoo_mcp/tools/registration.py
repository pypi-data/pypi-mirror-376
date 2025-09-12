"""
Tool registration utilities

Centralized functions for registering different categories of MCP tools
"""

from mcp.server.fastmcp import FastMCP
from ..utils.db_helpers import get_formatted_db_name


def register_all_tools(mcp: FastMCP):
    """Register all available MCP tools with the server"""
    db_name = get_formatted_db_name()
    
    # Register tools by category
    register_core_tools(mcp, db_name)
    register_batch_tools(mcp, db_name)
    register_search_tools(mcp, db_name)
    register_metadata_tools(mcp, db_name)
    register_export_tools(mcp, db_name)
    register_security_tools(mcp, db_name)
    register_workflow_tools(mcp, db_name)
    register_employee_tools(mcp, db_name)
    register_holiday_tools(mcp, db_name)


def register_core_tools(mcp: FastMCP, db_name: str):
    """Register core execution tools"""
    from ..tools.execute import execute_method
    
    mcp.tool(
        f"{db_name}_execute_method", 
        description=f"Execute a custom method on an Odoo model in {db_name}"
    )(execute_method)


def register_employee_tools(mcp: FastMCP, db_name: str):
    """Register all employee-related tools"""
    # Import base functions directly instead of using register_tools
    from ..tools.employee.base import search_employee, get_employee_details
    
    # Register standard employee tools
    mcp.tool(
        f"{db_name}_search_employee", 
        description=f"Search for employees by name in {db_name}"
    )(search_employee)
    
    mcp.tool(
        f"{db_name}_get_employee_details", 
        description=f"Get detailed information about an employee in {db_name}"
    )(get_employee_details)
    
    # Register Aspire-specific employee tools
    from ..tools.employee.aspire import (
        get_employee_driver_info,
        get_employee_banking_info,
        get_employee_payslips,
        get_employee_contracts,
        get_employee_attendance,
        get_employee_leaves,
        get_employee_appraisals,
        get_employee_financial_records
    )
    
    # Only register these if they're needed - we let each function handle its own
    # validation for required models/fields
    
    mcp.tool(
        f"{db_name}_get_employee_driver_info", 
        description=f"Get driver information for an employee in {db_name}"
    )(get_employee_driver_info)
    
    mcp.tool(
        f"{db_name}_get_employee_banking_info", 
        description=f"Get banking information for an employee in {db_name}"
    )(get_employee_banking_info)
    
    mcp.tool(
        f"{db_name}_get_employee_payslips", 
        description=f"Get payslip information for an employee in {db_name}"
    )(get_employee_payslips)
    
    mcp.tool(
        f"{db_name}_get_employee_contracts", 
        description=f"Get contract information for an employee in {db_name}"
    )(get_employee_contracts)
    
    mcp.tool(
        f"{db_name}_get_employee_attendance", 
        description=f"Get attendance records for an employee in {db_name}"
    )(get_employee_attendance)
    
    mcp.tool(
        f"{db_name}_get_employee_leaves", 
        description=f"Get leave records for an employee in {db_name}"
    )(get_employee_leaves)
    
    mcp.tool(
        f"{db_name}_get_employee_appraisals", 
        description=f"Get appraisal records for an employee in {db_name}"
    )(get_employee_appraisals)
    
    mcp.tool(
        f"{db_name}_get_employee_financial_records", 
        description=f"Get financial records for an employee in {db_name}"
    )(get_employee_financial_records)


def register_holiday_tools(mcp: FastMCP, db_name: str):
    """Register holiday-related tools"""
    from ..tools.holiday import search_holidays
    
    mcp.tool(
        f"{db_name}_search_holidays", 
        description=f"Search for holidays within a date range in {db_name}"
    )(search_holidays)


def register_batch_tools(mcp: FastMCP, db_name: str):
    """Register batch operation tools"""
    from ..tools.batch import (
        batch_execute, batch_create, batch_update, 
        batch_delete, batch_copy
    )
    
    mcp.tool(
        f"{db_name}_batch_execute",
        description=f"Execute multiple operations in batch in {db_name}"
    )(batch_execute)
    
    mcp.tool(
        f"{db_name}_batch_create",
        description=f"Create multiple records at once in {db_name}"
    )(batch_create)
    
    mcp.tool(
        f"{db_name}_batch_update",
        description=f"Update multiple records with different values in {db_name}"
    )(batch_update)
    
    mcp.tool(
        f"{db_name}_batch_delete",
        description=f"Delete multiple records in {db_name}"
    )(batch_delete)
    
    mcp.tool(
        f"{db_name}_batch_copy",
        description=f"Copy/duplicate multiple records in {db_name}"
    )(batch_copy)


def register_search_tools(mcp: FastMCP, db_name: str):
    """Register advanced search tools"""
    from ..tools.search import (
        advanced_search, search_with_aggregation, 
        search_distinct, fuzzy_search
    )
    
    mcp.tool(
        f"{db_name}_advanced_search",
        description=f"Advanced search with complex filtering in {db_name}"
    )(advanced_search)
    
    mcp.tool(
        f"{db_name}_search_with_aggregation",
        description=f"Search with GROUP BY aggregation in {db_name}"
    )(search_with_aggregation)
    
    mcp.tool(
        f"{db_name}_search_distinct",
        description=f"Get distinct values for a field in {db_name}"
    )(search_distinct)
    
    mcp.tool(
        f"{db_name}_fuzzy_search",
        description=f"Fuzzy search across multiple fields in {db_name}"
    )(fuzzy_search)


def register_metadata_tools(mcp: FastMCP, db_name: str):
    """Register metadata and schema tools"""
    from ..tools.metadata import (
        get_field_metadata, get_model_constraints,
        get_model_relations, get_model_methods, get_model_views
    )
    
    mcp.tool(
        f"{db_name}_get_field_metadata",
        description=f"Get detailed field metadata for a model in {db_name}"
    )(get_field_metadata)
    
    mcp.tool(
        f"{db_name}_get_model_constraints",
        description=f"Get model constraints (SQL and Python) in {db_name}"
    )(get_model_constraints)
    
    mcp.tool(
        f"{db_name}_get_model_relations",
        description=f"Get all relationships for a model in {db_name}"
    )(get_model_relations)
    
    mcp.tool(
        f"{db_name}_get_model_methods",
        description=f"Get available methods for a model in {db_name}"
    )(get_model_methods)
    
    mcp.tool(
        f"{db_name}_get_model_views",
        description=f"Get view definitions for a model in {db_name}"
    )(get_model_views)


def register_export_tools(mcp: FastMCP, db_name: str):
    """Register data export/import tools"""
    from ..tools.export import (
        export_data, import_data, export_template
    )
    
    mcp.tool(
        f"{db_name}_export_data",
        description=f"Export data in various formats (JSON, CSV, XML) from {db_name}"
    )(export_data)
    
    mcp.tool(
        f"{db_name}_import_data",
        description=f"Import data from JSON or CSV into {db_name}"
    )(import_data)
    
    mcp.tool(
        f"{db_name}_export_template",
        description=f"Generate import template for a model in {db_name}"
    )(export_template)


def register_security_tools(mcp: FastMCP, db_name: str):
    """Register security and access control tools"""
    from ..tools.security import (
        get_user_info, get_model_access_rights,
        check_field_access, get_user_groups, sudo_execute
    )
    
    mcp.tool(
        f"{db_name}_get_user_info",
        description=f"Get information about a user in {db_name}"
    )(get_user_info)
    
    mcp.tool(
        f"{db_name}_get_model_access_rights",
        description=f"Get access rights for a model in {db_name}"
    )(get_model_access_rights)
    
    mcp.tool(
        f"{db_name}_check_field_access",
        description=f"Check field-level access rights in {db_name}"
    )(check_field_access)
    
    mcp.tool(
        f"{db_name}_get_user_groups",
        description=f"Get groups for a user in {db_name}"
    )(get_user_groups)
    
    mcp.tool(
        f"{db_name}_sudo_execute",
        description=f"Execute method with elevated privileges in {db_name}"
    )(sudo_execute)


def register_workflow_tools(mcp: FastMCP, db_name: str):
    """Register workflow and state management tools"""
    from ..tools.workflow import (
        get_record_state, execute_workflow_action,
        get_available_actions, bulk_state_transition,
        get_workflow_history
    )
    
    mcp.tool(
        f"{db_name}_get_record_state",
        description=f"Get current state of records in {db_name}"
    )(get_record_state)
    
    mcp.tool(
        f"{db_name}_execute_workflow_action",
        description=f"Execute workflow action on records in {db_name}"
    )(execute_workflow_action)
    
    mcp.tool(
        f"{db_name}_get_available_actions",
        description=f"Get available workflow actions for a record in {db_name}"
    )(get_available_actions)
    
    mcp.tool(
        f"{db_name}_bulk_state_transition",
        description=f"Perform bulk state transitions in {db_name}"
    )(bulk_state_transition)
    
    mcp.tool(
        f"{db_name}_get_workflow_history",
        description=f"Get workflow transition history for a record in {db_name}"
    )(get_workflow_history)
