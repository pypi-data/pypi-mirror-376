from typing import Dict, List, Optional
import logging
import pickle

from .tool import Tool
from .precallable_tool import PrecallTool, ExecutionMode
from .exceptions.toolbox_exceptions import (
    ToolBoxError,
    ToolValidationError,
    DuplicateToolError,
)
from .logging_utils import log_structured

logger = logging.getLogger(__name__)




class ToolBox:
    def __init__(self, tools: Optional[List[Tool]] = None, precall_tools: Optional[List[PrecallTool]] = None):
        """
        The ToolBox class acts as a container for all the tools that will be available to the Architect.

        Args:
            tools: A list of normal Tool objects to add to the ToolBox.
            precall_tools: A list of PrecallTool objects to add to the ToolBox.
        """
        self.tools: Dict[str, Tool] = {}
        self.precall_tools: Dict[str, PrecallTool] = {}
        
        total_count = 0
        if tools:
            total_count += len(tools)
            self._validate_and_add_tools(tools)
        if precall_tools:
            total_count += len(precall_tools)
            self._validate_and_add_precall_tools(precall_tools)
            
        if total_count > 0:
            log_structured(logger, "info", "Initializing ToolBox", tool_count=len(self.tools), precall_tool_count=len(self.precall_tools), total_count=total_count)
        else:
            log_structured(logger, "info", "Initialized empty ToolBox")

    def add_tool(self, tool: Tool) -> None:
        """
        Adds a Tool object to the ToolBox.

        Args:
            tool: The Tool object to add to the ToolBox.
        """
        if not hasattr(tool, "tool_name"):
            log_structured(logger, "error", "Failed to add tool - missing tool_name attribute", tool_type=type(tool).__name__)
            raise ToolValidationError(
                "Tool must have a tool_name attribute",
                tool_type=type(tool).__name__
            )
        if tool.tool_name in self.tools or tool.tool_name in self.precall_tools:
            log_structured(logger, "error", "Failed to add tool - name already exists", tool_name=tool.tool_name)
            raise DuplicateToolError(tool.tool_name)
        
        # Validate PROCESS tools can be pickled early
        if hasattr(tool, 'execution_mode') and tool.execution_mode == ExecutionMode.PROCESS:
            try:
                pickle.dumps(tool)
                log_structured(logger, "debug", "PROCESS tool pickle validation passed", tool_name=tool.tool_name)
            except Exception as e:
                log_structured(logger, "error", "PROCESS tool failed pickle validation", tool_name=tool.tool_name, error=str(e))
                raise ToolValidationError(
                    f"PROCESS tool '{tool.tool_name}' must be pickleable but failed validation: {e}",
                    tool_type=type(tool).__name__,
                    tool_name=tool.tool_name
                )
        
        self.tools[tool.tool_name] = tool
        log_structured(logger, "debug", "Added tool to ToolBox", tool_name=tool.tool_name, tool_type="normal")

    def add_precall_tool(self, precall_tool: PrecallTool) -> None:
        """
        Adds a PrecallTool object to the ToolBox.

        Args:
            precall_tool: The PrecallTool object to add to the ToolBox.
        """
        if not hasattr(precall_tool, "tool_name"):
            log_structured(logger, "error", "Failed to add precall tool - missing tool_name attribute", tool_type=type(precall_tool).__name__)
            raise ToolValidationError(
                "PrecallTool must have a tool_name attribute",
                tool_type=type(precall_tool).__name__
            )
        if precall_tool.tool_name in self.tools or precall_tool.tool_name in self.precall_tools:
            log_structured(logger, "error", "Failed to add precall tool - name already exists", tool_name=precall_tool.tool_name)
            raise DuplicateToolError(precall_tool.tool_name)
        
        # Validate PROCESS precall tools can be pickled early
        if hasattr(precall_tool, 'execution_mode') and precall_tool.execution_mode == ExecutionMode.PROCESS:
            try:
                pickle.dumps(precall_tool)
                log_structured(logger, "debug", "PROCESS precall tool pickle validation passed", tool_name=precall_tool.tool_name)
            except Exception as e:
                log_structured(logger, "error", "PROCESS precall tool failed pickle validation", tool_name=precall_tool.tool_name, error=str(e))
                raise ToolValidationError(
                    f"PROCESS precall tool '{precall_tool.tool_name}' must be pickleable but failed validation: {e}",
                    tool_type=type(precall_tool).__name__,
                    tool_name=precall_tool.tool_name
                )
        
        self.precall_tools[precall_tool.tool_name] = precall_tool
        log_structured(logger, "debug", "Added precall tool to ToolBox", tool_name=precall_tool.tool_name, tool_type="precall")

    def set_tool_list(self, tools: List[Tool]) -> None:
        """
        Sets the list of Tool objects to the ToolBox, removing any existing tools.

        Args:
            tools: A list of Tool objects to set in the ToolBox.
        """
        old_count = len(self.tools)
        self.tools = {}
        self._validate_and_add_tools(tools)
        log_structured(logger, "info", "Updated tool list in ToolBox", old_count=old_count, new_count=len(tools))

    def set_precall_tool_list(self, precall_tools: List[PrecallTool]) -> None:
        """
        Sets the list of PrecallTool objects to the ToolBox, removing any existing precall tools.

        Args:
            precall_tools: A list of PrecallTool objects to set in the ToolBox.
        """
        old_count = len(self.precall_tools)
        self.precall_tools = {}
        self._validate_and_add_precall_tools(precall_tools)
        log_structured(logger, "info", "Updated precall tool list in ToolBox", old_count=old_count, new_count=len(precall_tools))

    def find_by_tool_name(self, tool_name: str) -> Optional[Tool]:
        """
        Finds a normal Tool object by its tool_name.

        Args:
            tool_name: The name of the Tool object to find.

        Returns:
            Tool: The Tool object if found, otherwise None.
        """
        tool = self.tools.get(tool_name)
        if tool:
            log_structured(logger, "debug", "Found tool by name", tool_name=tool_name, tool_type="normal")
        else:
            log_structured(logger, "warning", "Tool not found by name", tool_name=tool_name, available_tools=list(self.tools.keys()))
        return tool

    def find_precall_tool_by_name(self, tool_name: str) -> Optional[PrecallTool]:
        """
        Finds a PrecallTool object by its tool_name.

        Args:
            tool_name: The name of the PrecallTool object to find.

        Returns:
            PrecallTool: The PrecallTool object if found, otherwise None.
        """
        precall_tool = self.precall_tools.get(tool_name)
        if precall_tool:
            log_structured(logger, "debug", "Found precall tool by name", tool_name=tool_name, tool_type="precall")
        else:
            log_structured(logger, "warning", "Precall tool not found by name", tool_name=tool_name, available_precall_tools=list(self.precall_tools.keys()))
        return precall_tool

    def remove_tool(self, tool_name: str) -> None:
        """
        Removes a Tool object from the ToolBox.

        Args:
            tool_name: The name of the Tool object to remove.
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            log_structured(logger, "debug", "Removed tool from ToolBox", tool_name=tool_name, tool_type="normal")
        else:
            log_structured(logger, "warning", "Attempted to remove non-existent tool", tool_name=tool_name)

    def remove_precall_tool(self, tool_name: str) -> None:
        """
        Removes a PrecallTool object from the ToolBox.

        Args:
            tool_name: The name of the PrecallTool object to remove.
        """
        if tool_name in self.precall_tools:
            del self.precall_tools[tool_name]
            log_structured(logger, "debug", "Removed precall tool from ToolBox", tool_name=tool_name, tool_type="precall")
        else:
            log_structured(logger, "warning", "Attempted to remove non-existent precall tool", tool_name=tool_name)

    def open_tool(self, tool_name: str) -> Optional[str]:
        """
        Creates a string representation of a Tool object formatted for consumption by an Large Language Model.

        Args:
            tool_name: The name of the Tool object to open.

        Returns:
            str: A string representation of the Tool object
        """
        tool: Optional[Tool] = self.tools.get(tool_name)
        if not tool:
            return None
        tool_details: str = f"TOOL NAME: {tool.tool_name}\n"
        tool_details += f"Usage Context: {tool.usage_context}\n"
        tool_details += f"Purpose: {tool.purpose}\n"
        tool_details += "Parameter Instructions:\n"
        for param_name, (data_type, description) in tool.parameter_instructions.items():
            tool_details += f"  {param_name} ({data_type}): {description}\n"
        tool_details += "\nOutput Descriptions:\n"
        for output_name, (data_type, description) in tool.output_descriptions.items():
            tool_details += f"  {output_name} ({data_type}): {description}\n"
        return tool_details

    def open_all_tools(self) -> str:
        """
        Opens each normal tool and appends the details to a single string.
        (Note: This only includes normal tools, not precall tools)

        Returns:
            str: A string representation of all the normal Tool objects in the ToolBox.
        """
        all_tool_details: str = "TOOLS:\n--------------------------------\n"
        for tool_name in self.tools.keys():
            tool_details: Optional[str] = self.open_tool(tool_name)
            if tool_details:
                all_tool_details += tool_details + "\n"
        return all_tool_details

    def _validate_and_add_tools(self, tools: List[Tool]) -> None:
        """
        Validates the tools and adds them to the ToolBox.

        Args:
            tools: A list of Tool objects to add to the ToolBox.
        """
        for tool in tools:
            if not hasattr(tool, "tool_name"):
                log_structured(logger, "error", "Tool validation failed - missing tool_name attribute", tool_type=type(tool).__name__)
                raise ToolValidationError(
                    "Tool must have a tool_name attribute",
                    tool_type=type(tool).__name__
                )
            if tool.tool_name in self.tools or tool.tool_name in self.precall_tools:
                log_structured(logger, "error", "Tool validation failed - duplicate tool_name", tool_name=tool.tool_name)
                raise DuplicateToolError(tool.tool_name)
            
            # Validate PROCESS tools can be pickled early
            if hasattr(tool, 'execution_mode') and tool.execution_mode == ExecutionMode.PROCESS:
                try:
                    pickle.dumps(tool)
                    log_structured(logger, "debug", "PROCESS tool pickle validation passed", tool_name=tool.tool_name)
                except Exception as e:
                    log_structured(logger, "error", "PROCESS tool failed pickle validation", tool_name=tool.tool_name, error=str(e))
                    raise ToolValidationError(
                        f"PROCESS tool '{tool.tool_name}' must be pickleable but failed validation: {e}",
                        tool_type=type(tool).__name__,
                        tool_name=tool.tool_name
                    )
            
            self.tools[tool.tool_name] = tool
        log_structured(logger, "info", "Successfully validated and added normal tools", count=len(tools))

    def _validate_and_add_precall_tools(self, precall_tools: List[PrecallTool]) -> None:
        """
        Validates the precall tools and adds them to the ToolBox.

        Args:
            precall_tools: A list of PrecallTool objects to add to the ToolBox.
        """
        for precall_tool in precall_tools:
            if not hasattr(precall_tool, "tool_name"):
                log_structured(logger, "error", "Precall tool validation failed - missing tool_name attribute", tool_type=type(precall_tool).__name__)
                raise ToolValidationError(
                    "PrecallTool must have a tool_name attribute",
                    tool_type=type(precall_tool).__name__
                )
            if precall_tool.tool_name in self.tools or precall_tool.tool_name in self.precall_tools:
                log_structured(logger, "error", "Precall tool validation failed - duplicate tool_name", tool_name=precall_tool.tool_name)
                raise DuplicateToolError(precall_tool.tool_name)
            
            # Validate PROCESS precall tools can be pickled early
            if hasattr(precall_tool, 'execution_mode') and precall_tool.execution_mode == ExecutionMode.PROCESS:
                try:
                    pickle.dumps(precall_tool)
                    log_structured(logger, "debug", "PROCESS precall tool pickle validation passed", tool_name=precall_tool.tool_name)
                except Exception as e:
                    log_structured(logger, "error", "PROCESS precall tool failed pickle validation", tool_name=precall_tool.tool_name, error=str(e))
                    raise ToolValidationError(
                        f"PROCESS precall tool '{precall_tool.tool_name}' must be pickleable but failed validation: {e}",
                        tool_type=type(precall_tool).__name__,
                        tool_name=precall_tool.tool_name
                    )
            
            self.precall_tools[precall_tool.tool_name] = precall_tool
        log_structured(logger, "info", "Successfully validated and added precall tools", count=len(precall_tools))

    def open_non_precallable_tools(self) -> str:
        """
        Opens each normal tool and appends the details to a single string.
        This is used to provide LLM access to normal tools only (not precall tools).

        Returns:
            str: A string representation of all the normal Tool objects in the ToolBox.
        """
        return self.open_all_tools()  # Since we separated the tools, all normal tools are non-precallable

    def get_precallable_tools(self) -> List[PrecallTool]:
        """
        Fetches precall tools from the ToolBox.

        Returns:
            List[PrecallTool]: A list of all the PrecallTool objects in the ToolBox.
        """
        precallable_tools = list(self.precall_tools.values())
        log_structured(logger, "debug", "Retrieved precallable tools", count=len(precallable_tools), tool_names=[t.tool_name for t in precallable_tools])
        return precallable_tools
