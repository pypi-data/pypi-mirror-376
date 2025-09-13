"""
Architect AI - An AI-powered architecture planning system.
"""

from .architect import Architect
from .blueprint import Blueprint
from .blueprint_rack import (
    BlueprintRack,
    # Blueprint rack exceptions
    BlueprintRackError,
    BlueprintValidationError,
    DuplicateBlueprintError,
)
from .tool import Tool
from .toolbox import ToolBox
from .precallable_tool import (
    PrecallTool,
    ExecutionMode,
    PrecallableResultsProxy,
    PicklablePrecallableResults,
)
from .exceptions import (
    # Architect exceptions
    ArchitectError,
    PrecallableToolError,
    BuildPlanParsingError,
    BlueprintNotFoundError,
    ToolExecutionModeError,
    ToolExecutionError,
    ReferenceResolutionError,
    InvalidReferencePathError,
    StageValidationError,
    BuildPlanGenerationError,
    ToolPicklingError,
    # Tool exceptions
    ToolError,
    PrecallableToolNotFoundError,
    PrecallableToolExecutionError,
    PrecallableToolRuntimeError,
    # Toolbox exceptions
    ToolBoxError,
    ToolValidationError,
    DuplicateToolError,
)

__version__ = "0.1.0"
__all__ = [
    # Core classes
    "Architect",
    "Blueprint", 
    "BlueprintRack",
    "Tool",
    "PrecallTool",
    "ExecutionMode",
    "PrecallableResultsProxy", 
    "PicklablePrecallableResults",
    "ToolBox",
    # Architect exceptions
    "ArchitectError",
    "PrecallableToolError",
    "BuildPlanParsingError", 
    "BlueprintNotFoundError",
    "ToolExecutionModeError",
    "ToolExecutionError",
    "ReferenceResolutionError",
    "InvalidReferencePathError",
    "StageValidationError",
    "BuildPlanGenerationError",
    "ToolPicklingError",
    # Blueprint rack exceptions
    "BlueprintRackError",
    "BlueprintValidationError",
    "DuplicateBlueprintError",
    # Tool exceptions
    "ToolError",
    "PrecallableToolNotFoundError",
    "PrecallableToolExecutionError", 
    "PrecallableToolRuntimeError",
    # Toolbox exceptions
    "ToolBoxError",
    "ToolValidationError",
    "DuplicateToolError",
]
