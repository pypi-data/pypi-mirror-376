"""
PyConvexity - Python library for energy system modeling and optimization.

This library provides the core functionality of the Convexity desktop application
as a reusable, pip-installable package for building and solving energy system models.
"""

# Version information
from pyconvexity._version import __version__

__author__ = "Convexity Team"

# Core imports - always available
from pyconvexity.core.errors import (
    PyConvexityError,
    DatabaseError,
    ValidationError,
    ComponentNotFound,
    AttributeNotFound,
)

from pyconvexity.core.types import (
    StaticValue,
    TimeseriesPoint,
    Component,
    Network,
    CreateNetworkRequest,
    CreateComponentRequest,
)

from pyconvexity.core.database import (
    create_database_with_schema,
    database_context,
    open_connection,
    validate_database,
)

# Import main API functions
from pyconvexity.models import (
    # Component operations
    get_component, create_component, update_component, delete_component,
    list_components_by_type, list_component_attributes,
    
    # Attribute operations  
    set_static_attribute, set_timeseries_attribute, get_attribute, delete_attribute,
    
    # Network operations
    create_network, get_network_info, get_network_time_periods, list_networks,
    create_carrier, list_carriers, get_network_config, set_network_config,
    get_master_scenario_id, resolve_scenario_id,
)

from pyconvexity.validation import (
    get_validation_rule, list_validation_rules, validate_timeseries_alignment
)

# High-level API functions
__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Core types
    "StaticValue",
    "TimeseriesPoint", 
    "Component",
    "Network",
    "CreateNetworkRequest",
    "CreateComponentRequest",
    
    # Database operations
    "create_database_with_schema",
    "database_context", 
    "open_connection",
    "validate_database",
    
    # Exceptions
    "PyConvexityError",
    "DatabaseError",
    "ValidationError",
    "ComponentNotFound",
    "AttributeNotFound",
    
    # Component operations
    "get_component", "create_component", "update_component", "delete_component",
    "list_components_by_type", "list_component_attributes",
    
    # Attribute operations
    "set_static_attribute", "set_timeseries_attribute", "get_attribute", "delete_attribute",
    
    # Network operations
    "create_network", "get_network_info", "get_network_time_periods", "list_networks",
    "create_carrier", "list_carriers", "get_network_config", "set_network_config",
    "get_master_scenario_id", "resolve_scenario_id",
    
    # Validation
    "get_validation_rule", "list_validation_rules", "validate_timeseries_alignment",
]

# Optional imports with graceful fallbacks
try:
    from pyconvexity.solvers.pypsa import PyPSASolver
    __all__.append("PyPSASolver")
except ImportError:
    # PyPSA not available
    pass

try:
    from pyconvexity.io.excel import ExcelImporter, ExcelExporter
    __all__.extend(["ExcelImporter", "ExcelExporter"])
except ImportError:
    # Excel dependencies not available
    pass

try:
    from pyconvexity.io.netcdf import NetCDFImporter, NetCDFExporter
    __all__.extend(["NetCDFImporter", "NetCDFExporter"])
except ImportError:
    # NetCDF dependencies not available
    pass
