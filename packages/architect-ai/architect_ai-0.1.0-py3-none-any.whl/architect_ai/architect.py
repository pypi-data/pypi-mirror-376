from typing import List, Dict, Any, Optional, Tuple, Union
from openai import AsyncOpenAI
import asyncio
import json
import uuid
import psutil  # type: ignore
from concurrent.futures import ProcessPoolExecutor
import os
from .toolbox import ToolBox
from .blueprint_rack import BlueprintRack
from .blueprint import Blueprint
from .tool import Tool
from .precallable_tool import PrecallTool, ExecutionMode, PrecallableResultsProxy, PicklablePrecallableResults
from .exceptions.architect_exceptions import (
    PrecallableToolError,
    BuildPlanParsingError,
    BlueprintNotFoundError,
    ToolExecutionModeError,
    ToolExecutionError,
    ReferenceResolutionError,
    InvalidReferencePathError,
    StageValidationError,
    BuildPlanGenerationError,
    ToolNotFoundError,
)
from .logging_utils import log_structured
import time
import functools
import logging

logger = logging.getLogger(__name__)




def killtree(pid, including_parent=True):
    """
    Kill a process and all its children recursively.
    
    Args:
        pid: Process ID to kill
        including_parent: Whether to kill the parent process as well
    """
        
    try:
        parent = psutil.Process(pid)
        
        # Security check: only allow killing processes owned by current user
        current_user = psutil.Process().username()
        if parent.username() != current_user:
            log_structured(
                logger,
                "warning",
                "Refusing to kill process owned by different user",
                target_pid=pid,
                process_user=parent.username(),
                current_user=current_user
            )
            return
        
        children = parent.children(recursive=True)
        
        # Kill children first
        for child in children:
            try:
                # Same security checks for children
                if child.username() != current_user:
                    log_structured(
                        logger,
                        "warning",
                        "Skipping child process owned by different user",
                        child_pid=child.pid,
                        process_user=child.username(),
                        current_user=current_user
                    )
                    continue
                
                log_structured(
                    logger,
                    "info", 
                    f"Killing child process {child.pid}",
                    child_pid=child.pid,
                    process_name=child.name()
                )
                child.kill()
            except psutil.NoSuchProcess:
                pass  # Already dead
            except psutil.AccessDenied as e:
                log_structured(
                    logger,
                    "warning",
                    f"Access denied killing child process {child.pid}",
                    child_pid=child.pid,
                    error=str(e)
                )
        
        # Kill parent if requested
        if including_parent:
            try:
                log_structured(
                    logger,
                    "info", 
                    f"Killing parent process {parent.pid}",
                    parent_pid=parent.pid,
                    process_name=parent.name()
                )
                parent.kill()
            except psutil.NoSuchProcess:
                pass  # Already dead
            except psutil.AccessDenied as e:
                log_structured(
                    logger,
                    "warning",
                    f"Access denied killing parent process {parent.pid}",
                    parent_pid=parent.pid,
                    error=str(e)
                )
                
    except psutil.NoSuchProcess:
        # Process already dead
        pass
    except psutil.AccessDenied as e:
        log_structured(
            logger,
            "warning",
            f"Access denied accessing process {pid}",
            target_pid=pid,
            error=str(e)
        )


def _run_tool_for_process(tool, params=None, precallables=None):
    """Helper function for process execution - needs to be module-level for pickling."""
    if params is None:
        params = {}
    return tool.use(params, precallables)


def _get_current_pid() -> int:
    """Small helper executed in process pool to fetch worker PID."""
    return os.getpid()




class PrecallableToolState:
    """Tracks the state of a running precallable tool."""
    
    def __init__(self, tool: PrecallTool, awaitable: Union[asyncio.Task[Any], asyncio.Future[Any]]):
        self.tool = tool
        self.awaitable = awaitable
        self.is_completed = False
        self.is_killed = False
        self.result = None


class RequestState:
    """Holds per-request state to ensure thread-safety and proper cleanup."""
    
    def __init__(self, max_process_workers: Optional[int] = None):
        self.process_executor: Optional[ProcessPoolExecutor] = None
        self.running_precallables: Dict[str, PrecallableToolState] = {}
        self.process_worker_pids: set[int] = set()
        self.max_process_workers = max_process_workers
        self.cleanup_performed = False


class Architect:
    build_plan_generation_base_prompt = """
    You are an expert systems architect, named Arch, with 30 years of experience in the technology industry. Your primary objective is to generate a build plan that will outline exactly how to make use of the various tools at your disposal to meet the product owner's demands (the user with which you will be interacting is the product owner). You must also ensure that this information is documented correctly by filling in the parameters of any blueprints that are applicable to the customer's request. Each tool in your toolbox comes with a guide that details when to use it, what it does, and how to format the input parameters to get your desired output parameters. Each blueprint on the blueprint rack comes with a guide that details when to use it and how to correctly fill in the parameters to ensure that your work has been correctly documented. 

    The final deliverable will be a JSON representation of the build plan constructed such that there is no room for ambiguity. There are two types of "top level" keys that should be present in the JSON. First, there should be a series of numbered "stage" keys ('stage_1', 'stage_2', etc.) that each contain a list of tools and their respective input parameters. Each tool contained within a stage will be executed in parallel. Once all the tools in a stage have returned, the next stage will begin. Subsequent stages will have access to the outputs of the previous stages. Where possible, make full use of parallel execution to maximize efficiency, including multiple tools in the same stage. To include tool calls within a stage, you should use the following format:

    {{
        "stage_1": {{
            "tool_name_1": {{
                "input_param_1": "text_value_1",
                "input_param_2": 8,
            }}
            "tool_name_2": {{
                "input_param_1": "text_value_1",
            }}
        }}
        ...
    }}

    Tool calls in subsequent stages will often need to reference the outputs of the previous stages. To make use of this ability, you should use the format $ref.stage_name.tool_name.output_param_name anywhere within strings, lists, or nested structures. References can be mixed with regular values. See the following example:

    {{
        "stage_1": {{
            "tool_name_1": {{
                "input_param_1": "text_value_1",
            }}
        }}
        "stage_2": {{
            "tool_name_2": {{
                "input_param_1": "Processing result: $ref.stage_1.tool_name_1.output_param_1",
                "input_param_2": ["item1", 42, "$ref.stage_1.tool_name_1.output_param_2"],
                "input_param_3": "$ref.stage_1.tool_name_1.output_param_1"
            }}
        }}
    }}

    The other top level keys in the JSON object must be the names of the blueprint(s) that are applicable to the customer's request. These will be mapped to a list of input parameters for that respective blueprint. Again, each blueprint will come with instructions as to when to use it and how to correctly fill in the parameters. Here is an example of how the final JSON object should look. However, keep in mind that the number of stages and blueprints required will vary based on the customer's request.

    {{
        "stage_1": {{
            "tool_name_1": {{
                "input_param_1": "text_value_1",
            }}
            ...
        }}
        "stage_2": {{
            "tool_name_2": {{
                "input_param_1": "$ref.stage_1.tool_name_1.output_param_1"
            }}
            "tool_name_3": {{
                "input_param_1": "text_value_1",
            }}
            ...
        }}
        ...
        "blueprint_1": {{
            "input_param_1": "text_value_1",
            "input_param_2": "$ref.stage_2.tool_name_2.output_param_1"
        }}
        "blueprint_2": {{
            "input_param_1": "$ref.stage_2.tool_name_3.output_param_3",
            "input_param_2": "$ref.stage_1.tool_name_1.output_param_1"
        }}
        ...
    }}

    HERE IS YOUR TOOLBOX:
    --------------------------------
    {toolbox}
    --------------------------------

    HERE IS YOUR BLUEPRINT RACK:
    --------------------------------
    {blueprint_rack}
    --------------------------------

    CRITICAL INSTRUCTIONS:
    - NEVER use any input or output parameter names for tools or blueprints that are not explicitly listed in the toolbox or the blueprint rack, respectively.
    - NEVER produce an incomplete output or use any placeholders of your own invention. If you are unable to call a tool or fill a blueprint accurately, you still must make sure that your build plan will compile successfully.
    - Input parameters can be simple values, strings with embedded references, lists containing mixed values and references, or nested structures. References using $ref.stage.tool.output format will be resolved recursively.
    - NEVER try to index a variable like $ref.stage_1.tool_1.output_list[0:2] - references cannot be sliced.

    PROCESS TOOL OPTIMIZATION:
    - For PROCESS execution mode tools, you can optionally specify which precallable tools they need to wait for by adding a special "_required_precallables" parameter.
    - This parameter should be a list of precallable tool names, e.g. "_required_precallables": ["precallable_async_tool"].
    - If not specified, process tools will wait for ALL precallables to complete (safe but potentially slower).
    - Use this optimization when you know a process tool only needs specific precallables, not all of them.
    - Example: {{"process_fetch_tool": {{"fetch_from": "async", "_required_precallables": ["precallable_async_tool"]}}}}
    - This parameter is ignored for ASYNC and THREAD tools (they can access precallables as needed).

    REPEATED FORMATTING EXAMPLE FOR REFERENCE:
    --------------------------------
    {{
        "stage_1": {{
            "tool_name_1": {{
                "input_param_1": "text_value_1",
            }}
            ...
        }}
        "stage_2": {{
            "tool_name_2": {{
                "input_param_1": "$ref.stage_1.tool_name_1.output_param_1"
            }}
            "tool_name_3": {{
                "input_param_1": "text_value_1",
            }}
            ...
        }}
        ...
        "blueprint_1": {{
            "input_param_1": "text_value_1",
            "input_param_2": "$ref.stage_2.tool_name_2.output_param_1"
        }}
        "blueprint_2": {{
            "input_param_1": "$ref.stage_2.tool_name_3.output_param_3",
            "input_param_2": "$ref.stage_1.tool_name_1.output_param_1"
        }}
        ...
    }}
    --------------------------------

    """

    build_plan_additional_context_prompt_wrapper = """
    URGENT UPDATE: The product owner has provided additional information! All new information should be utilized as needed, and any new instructions must be followed exactly. Do your best to fulfill all requirements, which will generally be possible, but in the event of a contradiction, these updates must take precedence over the original requirements:

    --------------------------------
    {additional_context_prompt}
    --------------------------------

    Regardless of any new information, you must still return a valid build plan that will compile successfully according to the previous formatting instructions.
    """

    build_plan_previous_attempt_error_message_prompt_wrapper = """
    CORRECTION NEEDED: The product owner has informed us that on the previous attempt to generate and executea build plan, the following error message was returned:
    --------------------------------
    {previous_attempt_error_message}
    --------------------------------
    
    This error message should be taken into account when generating the next build plan to avoid making the same mistake. Never include details from this message in the build plan, but use it to guide the structure of the build plan so that the same error doesn't happen again.
    """

    user_prompt_wrapper = """
    Hi, Arch. Product owner here. Generate a build plan for the following customer request:
    --------------------------------
    {customer_request}
    --------------------------------

    Here is the conversation history with the customer:
    --------------------------------
    {conversation_history}
    --------------------------------

    And once again here is the initial request that you should focus on fulfilling:
    --------------------------------
    {customer_request}
    --------------------------------
    """

    def __init__(
        self,
        openai_client: AsyncOpenAI,
        model_name: str,
        toolbox: ToolBox,
        blueprint_rack: BlueprintRack,
        max_process_workers: Optional[int] = None,
    ):
        """
        Initialize the Architect with configuration options.
        
        Args:
            openai_client: AsyncOpenAI client for LLM communication
            model_name: Name of the model to use for build plan generation
            toolbox: Container of available tools
            blueprint_rack: Container of available blueprints
            max_process_workers: Maximum number of process workers for ProcessPoolExecutor.
                               If None, uses ProcessPoolExecutor default (number of CPUs).
            
        """
        self.openai_client = openai_client
        self.model_name = model_name
        self.toolbox = toolbox
        self.blueprint_rack = blueprint_rack
        self.max_process_workers = max_process_workers
        log_structured(
            logger,
            "warning",  # Changed from info to warning for library usage
            "Architect initialized",
            tool_count=len(toolbox.tools),
            precall_tool_count=len(toolbox.precall_tools),
            blueprint_count=len(blueprint_rack.blueprints),
            model_name=model_name,
            max_process_workers=max_process_workers,
        )

    async def _ensure_process_worker_pids_initialized(self, request_state: RequestState, loop: asyncio.AbstractEventLoop) -> None:
        """
        Populate the set of worker PIDs for our ProcessPoolExecutor more deterministically.
        This ensures we can properly terminate workers if needed.
        """
        if request_state.process_executor is None:
            return
        if request_state.process_worker_pids:
            return
            
        # Get actual max workers from executor or our configuration
        max_workers = self.max_process_workers or min(os.cpu_count() or 2, 8)
        
        try:
            # Submit exactly max_workers tasks to discover worker PIDs
            # Wait for unique PIDs to stabilize 
            collected_pids: set[int] = set()
            attempts = 0
            max_attempts = 3
            
            while len(collected_pids) < max_workers and attempts < max_attempts:
                tasks: List[asyncio.Future[int]] = []
                
                # Submit tasks equal to expected worker count
                for _ in range(max_workers):
                    fut: asyncio.Future[int] = loop.run_in_executor(request_state.process_executor, _get_current_pid)  # type: ignore
                    tasks.append(fut)
                
                # Wait for results with timeout
                results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=10.0)
                
                # Collect unique PIDs
                for res in results:
                    if isinstance(res, int):
                        collected_pids.add(res)
                
                attempts += 1
                
                # Small delay to let process pool stabilize
                if len(collected_pids) < max_workers and attempts < max_attempts:
                    await asyncio.sleep(0.1)
            
            request_state.process_worker_pids = collected_pids
            
            log_structured(
                logger,
                "info", 
                "Collected process worker PIDs",
                pid_count=len(request_state.process_worker_pids),
                max_workers=max_workers,
                attempts=attempts,
                complete=len(collected_pids) >= max_workers,
            )
            
        except asyncio.TimeoutError:
            log_structured(
                logger,
                "warning",
                "Timeout collecting worker PIDs - proceeding with best effort cleanup",
                collected_pids=len(request_state.process_worker_pids),
            )
        except Exception as e:
            log_structured(
                logger,
                "warning",
                "Failed to collect worker PIDs - proceeding with best effort cleanup",
                error=str(e),
                collected_pids=len(request_state.process_worker_pids),
            )

    def _start_precall_tools(
        self, request_state: RequestState, correlation_id: str, start_time: float
    ) -> Dict[str, Union[asyncio.Task[Any], asyncio.Future[Any]]]:
        """
        Launches all precallable tools in parallel using their optimal execution modes.

        Args:
            request_state: Per-request state container
            correlation_id (str): Unique identifier for this request.
            start_time (float): The start time of the generate_response call.

        Returns:
            Dict[str, Union[asyncio.Task[Any], asyncio.Future[Any]]]: A dictionary that maps tool names to their respective tasks/futures.
        """
        precallable_tools: List[PrecallTool] = self.toolbox.get_precallable_tools()
        if not precallable_tools:
            return {}

        current_time = time.perf_counter() - start_time
        log_structured(
            logger,
            "warning",
            "Starting precallable tools",
            correlation_id=correlation_id,
            perf_time=current_time,
            tool_count=len(precallable_tools),
        )

        precall_awaitables: Dict[
            str, Union[asyncio.Task[Any], asyncio.Future[Any]]
        ] = {}
        loop = asyncio.get_running_loop()

        try:
            for tool in precallable_tools:
                current_time = time.perf_counter() - start_time
                log_structured(
            logger,
                    "debug",
                    "Starting precallable tool",
                    correlation_id=correlation_id,
                    perf_time=current_time,
                    tool_name=tool.tool_name,
                    execution_mode=tool.execution_mode.value,
                )

                if tool.execution_mode == ExecutionMode.ASYNC:
                    # For async tools, create task without calling use() first to avoid sequential execution
                    async def run_async_tool(t=tool):
                        result = t.use({})
                        # If the tool returns a coroutine, await it
                        if asyncio.iscoroutine(result):
                            return await result
                        return result
                    
                    task = asyncio.create_task(run_async_tool())
                    
                    precall_awaitables[tool.tool_name] = task
                    # Track the tool state for lifecycle management
                    request_state.running_precallables[tool.tool_name] = PrecallableToolState(tool, task)

                elif tool.execution_mode == ExecutionMode.THREAD:
                    # For thread tools, use lambda to properly capture the tool
                    current_time = time.perf_counter() - start_time
                    log_structured(
            logger,
                        "warning",
                        "About to submit thread tool to executor",
                        correlation_id=correlation_id,
                        perf_time=current_time,
                        tool_name=tool.tool_name,
                    )
                    captured_tool = tool
                    future = loop.run_in_executor(None, lambda: captured_tool.use({}))
                    current_time = time.perf_counter() - start_time
                    log_structured(
            logger,
                        "warning",
                        "Thread tool submitted to executor",
                        correlation_id=correlation_id,
                        perf_time=current_time,
                        tool_name=tool.tool_name,
                    )
                    precall_awaitables[tool.tool_name] = future
                    # Track the tool state for lifecycle management
                    request_state.running_precallables[tool.tool_name] = PrecallableToolState(tool, future)
                
                elif tool.execution_mode == ExecutionMode.PROCESS:
                    # For process tools, use ProcessPoolExecutor to bypass GIL
                    current_time = time.perf_counter() - start_time
                    log_structured(
            logger,
                        "warning",
                        "About to submit process tool to executor",
                        correlation_id=correlation_id,
                        perf_time=current_time,
                        tool_name=tool.tool_name,
                    )
                    # Process tools need to use ProcessPoolExecutor
                    if request_state.process_executor is None:
                        request_state.process_executor = ProcessPoolExecutor(max_workers=self.max_process_workers)
                    
                    # Use module-level helper function that can be pickled
                    future = loop.run_in_executor(
                        request_state.process_executor, functools.partial(_run_tool_for_process, tool, {}, None)
                    )
                    current_time = time.perf_counter() - start_time
                    log_structured(
            logger,
                        "warning",
                        "Process tool submitted to executor",
                        correlation_id=correlation_id,
                        perf_time=current_time,
                        tool_name=tool.tool_name,
                    )
                    precall_awaitables[tool.tool_name] = future
                    # Track the tool state for lifecycle management
                    request_state.running_precallables[tool.tool_name] = PrecallableToolState(tool, future)

        except Exception as e:
            current_time = time.perf_counter() - start_time
            log_structured(
            logger,
                "error",
                "Failed to start precallable tools",
                correlation_id=correlation_id,
                perf_time=current_time,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise PrecallableToolError(
                f"Failed to start precallable tools: {e}",
                correlation_id=correlation_id,
                tool_count=len(precallable_tools),
                original_error=str(e),
                original_error_type=type(e).__name__
            )

        return precall_awaitables

    async def _generate_build_plan(
        self,
        customer_request: str,
        conversation_history: Any,
        additional_context_prompt: str,
        correlation_id: str,
        start_time: float,
        previous_attempt_error_message: Optional[str] = None,
        hedge_requests: int = 2,
    ) -> str:
        """
        Generates a build plan for the given customer request.

        Args:
            customer_request (str): The customer's current request.

            conversation_history (Any): The conversation history with the customer. The format of the conversation history does not have to precisely match what is generally expected by the LLM because the history is passed within the user prompt. Generally something like List[Dict[str, str]] works well.

            additional_context_prompt (str): Additional context from the product owner. This is passed within a developer prompt to allow the caller to have more control over how the build plan is generated. The format of the build plan must stay the same, but additional restrictions on what is allowed can be added.

            correlation_id (str): Unique identifier for this request.

            start_time (float): The start time of the generate_response call.

            previous_attempt_error_message (Optional[str]): The error message that was returned by the previous attempt to generate the same build plan. This will be passed to the LLM to help it avoid making the same mistake again.

        Returns:
            str: An executable build plan in JSON format.
        """
        initial_developer_prompt: str = self.build_plan_generation_base_prompt.format(
            toolbox=self.toolbox.open_non_precallable_tools(),
            blueprint_rack=self.blueprint_rack.open_all_blueprints(),
        )
        context_developer_prompt: str = (
            self.build_plan_additional_context_prompt_wrapper.format(
                additional_context_prompt=additional_context_prompt
            )
        )
        error_message_developer_prompt: Optional[str] = None
        if previous_attempt_error_message:
            error_message_developer_prompt = (
                self.build_plan_previous_attempt_error_message_prompt_wrapper.format(
                    previous_attempt_error_message=previous_attempt_error_message
                )
            )
        user_prompt: str = self.user_prompt_wrapper.format(
            conversation_history=conversation_history, customer_request=customer_request
        )
        messages: List[Dict[str, str]] = [
            {"role": "developer", "content": initial_developer_prompt},
            {"role": "developer", "content": context_developer_prompt},
            *(
                [{"role": "developer", "content": error_message_developer_prompt}]
                if error_message_developer_prompt
                else []
            ),
            {"role": "user", "content": user_prompt},
        ]
        current_time = time.perf_counter() - start_time
        log_structured(
            logger,
            "info",
            "Starting build plan generation with LLM",
            correlation_id=correlation_id,
            perf_time=current_time,
            message_count=len(messages),
            model_name=self.model_name,
        )

        async def make_request():
            current_time = time.perf_counter() - start_time
            log_structured(
            logger,
                "info",
                "Making OpenAI API call (precallable tools running in parallel)",
                correlation_id=correlation_id,
                perf_time=current_time,
                model_name=self.model_name,
            )
            return await self.openai_client.chat.completions.create(  # type: ignore
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"},
            )

        tasks = []
        for i in range(hedge_requests):
            if i > 0:
                await asyncio.sleep(0.01)
            # Create task explicitly for coroutines
            task = asyncio.create_task(make_request())
            tasks.append(task)

        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        response = next(iter(done)).result()

        # Cancel remaining tasks and suppress their exceptions
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass  # Expected when task is cancelled
        build_plan: str = response.choices[0].message.content or ""
        current_time = time.perf_counter() - start_time
        log_structured(
            logger,
            "debug",
            "Generated build plan",
            correlation_id=correlation_id,
            perf_time=current_time,
            build_plan_length=len(build_plan),
        )
        return build_plan

    async def _execute_build_plan(
        self,
        request_state: RequestState,
        build_plan: str,
        precall_awaitables: Dict[str, Union[asyncio.Task[Any], asyncio.Future[Any]]],
        correlation_id: str,
        start_time: float,
    ) -> Tuple[List[Blueprint], Dict[str, Dict[str, Any]]]:
        """
        Executes a build plan. The function will iterate through each stage in sequence, passing the outputs of the previous stage to the next stage. Once all stages have been executed, the function will fill in the included blueprints using both the directly available values and the outputs from the stage executions.

        Args:
            build_plan (str): An executable build plan in JSON format.

            precall_awaitables (Dict[str, Union[asyncio.Task[Any], asyncio.Future[Any]]]): A dictionary mapping precallable tool names to their respective tasks/futures.

            correlation_id (str): Unique identifier for this request.

            start_time (float): The start time of the generate_response call.

        Returns:
            Tuple[List[Blueprint], Dict[str, Dict[str, Any]]]: A tuple containing:
                - A list of blueprints that were filled
                - The stage outputs dictionary containing all tool execution results
        """
        try:
            plan: Dict[str, Any] = json.loads(build_plan)
            current_time = time.perf_counter() - start_time
            log_structured(
            logger,
                "debug",
                "Parsed build plan successfully",
                correlation_id=correlation_id,
                perf_time=current_time,
                top_level_keys=len(plan),
            )
        except json.JSONDecodeError as e:
            current_time = time.perf_counter() - start_time
            log_structured(
            logger,
                "error",
                "Failed to parse build plan JSON",
                correlation_id=correlation_id,
                perf_time=current_time,
                error=str(e),
                error_type=type(e).__name__,
                build_plan_preview=build_plan[:200] if build_plan else None,
            )
            raise BuildPlanParsingError(
                str(e),
                build_plan_preview=build_plan[:200] if build_plan else None,
                correlation_id=correlation_id,
                build_plan_length=len(build_plan) if build_plan else 0
            ) from e
        stage_outputs: Dict[str, Dict[str, Any]] = {}
        stages: Dict[str, Dict[str, Any]] = {}
        blueprint_configs: Dict[str, Any] = {}
        for key, value in plan.items():
            if key.startswith("stage_"):
                stages[key] = value
            else:
                blueprint_configs[key] = value
        def safe_stage_sort_key(stage_name: str) -> int:
            """Safely extract stage number for sorting."""
            try:
                return int(stage_name.split("_")[1])
            except (ValueError, IndexError) as e:
                raise InvalidReferencePathError(
                    f"Invalid stage name format in build plan: {stage_name}. Expected format: stage_N where N is a number",
                    correlation_id=correlation_id
                ) from e
        
        sorted_stages: List[str] = sorted(stages.keys(), key=safe_stage_sort_key)
        current_time = time.perf_counter() - start_time
        log_structured(
            logger,
            "debug",
            "Build plan analysis",
            correlation_id=correlation_id,
            perf_time=current_time,
            stage_count=len(stages),
            blueprint_count=len(blueprint_configs),
        )
        for stage_name in sorted_stages:
            stage_config: Dict[str, Any] = stages[stage_name]
            current_time = time.perf_counter() - start_time
            log_structured(
            logger,
                "info",
                "Executing stage",
                correlation_id=correlation_id,
                perf_time=current_time,
                stage_name=stage_name,
                tool_count=len(stage_config),
            )
            stage_results: Dict[str, Any] = await self._execute_stage(
                request_state,
                stage_name,
                stage_config,
                stage_outputs,
                precall_awaitables,
                correlation_id,
                start_time,
            )
            stage_outputs[stage_name] = stage_results
            current_time = time.perf_counter() - start_time
            log_structured(
            logger,
                "info",
                "Completed stage",
                correlation_id=correlation_id,
                perf_time=current_time,
                stage_name=stage_name,
            )
        filled_blueprints: List[Blueprint] = []
        if blueprint_configs:
            current_time = time.perf_counter() - start_time
            log_structured(
            logger,
                "info",
                "Filling blueprints",
                correlation_id=correlation_id,
                perf_time=current_time,
                blueprint_count=len(blueprint_configs),
            )
        for blueprint_name, blueprint_params in blueprint_configs.items():
            current_time = time.perf_counter() - start_time
            log_structured(
            logger,
                "debug",
                "Processing blueprint",
                correlation_id=correlation_id,
                perf_time=current_time,
                blueprint_name=blueprint_name,
            )
            blueprint: Optional[Blueprint] = self.blueprint_rack.find_by_blueprint_name(
                blueprint_name
            )
            if blueprint:
                resolved_params: Dict[str, Any] = self._resolve_references(
                    blueprint_params, stage_outputs, None, correlation_id, start_time
                )
                blueprint.fill(resolved_params)
                filled_blueprints.append(blueprint)
                current_time = time.perf_counter() - start_time
                log_structured(
            logger,
                    "debug",
                    "Successfully filled blueprint",
                    correlation_id=correlation_id,
                    perf_time=current_time,
                    blueprint_name=blueprint_name,
                )
            else:
                current_time = time.perf_counter() - start_time
                log_structured(
            logger,
                    "error",
                    "Blueprint not found in blueprint rack",
                    correlation_id=correlation_id,
                    perf_time=current_time,
                    blueprint_name=blueprint_name,
                )
                raise BlueprintNotFoundError(
                    blueprint_name,
                    correlation_id=correlation_id
                )
        current_time = time.perf_counter() - start_time
        log_structured(
            logger,
            "info",
            "Completed build plan execution",
            correlation_id=correlation_id,
            perf_time=current_time,
            filled_blueprint_count=len(filled_blueprints),
        )
        return filled_blueprints, stage_outputs

    async def _execute_stage(
        self,
        request_state: RequestState,
        stage_name: str,
        stage_config: Dict[str, Any],
        stage_outputs: Dict[str, Dict[str, Any]],
        precall_awaitables: Dict[str, Union[asyncio.Task[Any], asyncio.Future[Any]]],
        correlation_id: str,
        start_time: float,
    ) -> Dict[str, Any]:
        """
        Executes a stage of the build plan after resolving all references using mixed execution modes.

        Args:
            stage_name (str): The name of the current stage.
            stage_config (Dict[str, Any]): The configuration for the stage.
            stage_outputs (Dict[str, Dict[str, Any]]): The outputs of the previous stages.
            precall_awaitables (Dict[str, Union[asyncio.Task[Any], asyncio.Future[Any]]]): The tasks/futures of the precallable tools.
            correlation_id (str): Unique identifier for this request.
            start_time (float): The start time of the generate_response call.

        Returns:
            Dict[str, Any]: The results of the stage.
        """
        if not stage_config:
            return {}

        try:
            current_stage_num = int(stage_name.split("_")[1])
        except (ValueError, IndexError) as e:
            raise InvalidReferencePathError(
                f"Invalid stage name format: {stage_name}. Expected format: stage_N where N is a number",
                correlation_id=correlation_id
            ) from e
        resolved_stage_config = self._resolve_references(
            stage_config, stage_outputs, current_stage_num, correlation_id, start_time
        )

        # Create proxy for lazy access to precallable results
        precallables = PrecallableResultsProxy(
            precall_awaitables, asyncio.get_running_loop()
        )

        # Group tools by execution mode for optimal execution
        async_tools = {}
        thread_tools = {}
        process_tools = {}
        loop = asyncio.get_running_loop()

        for tool_name, tool_params in resolved_stage_config.items():
            tool: Optional[Tool] = self.toolbox.find_by_tool_name(tool_name)
            if tool:
                current_time = time.perf_counter() - start_time
                log_structured(
            logger,
                    "debug",
                    "Starting tool in stage",
                    correlation_id=correlation_id,
                    perf_time=current_time,
                    tool_name=tool_name,
                    stage_name=stage_name,
                    execution_mode=tool.execution_mode.value,
                )

                if tool.execution_mode == ExecutionMode.ASYNC:
                    async_tools[tool_name] = (tool, tool_params)
                elif tool.execution_mode == ExecutionMode.THREAD:
                    thread_tools[tool_name] = (tool, tool_params)
                elif tool.execution_mode == ExecutionMode.PROCESS:
                    process_tools[tool_name] = (tool, tool_params)
            else:
                current_time = time.perf_counter() - start_time
                log_structured(
            logger,
                    "error",
                    "Tool not found in toolbox",
                    correlation_id=correlation_id,
                    perf_time=current_time,
                    tool_name=tool_name,
                    stage_name=stage_name,
                    available_tools=list(self.toolbox.tools.keys()),
                )
                raise ToolNotFoundError(
                    tool_name,
                    stage_name,
                    available_tools=list(self.toolbox.tools.keys()),
                    correlation_id=correlation_id,
                )

        # Execute each group with optimal strategy
        all_tasks: List[Union[asyncio.Task[Any], asyncio.Future[Any]]] = []
        tool_name_mapping = {}

        # ASYNC tools: run directly in event loop
        for tool_name, (tool, tool_params) in async_tools.items():
            result = tool.use(tool_params, precallables)
            if asyncio.iscoroutine(result):
                task = asyncio.create_task(result)
            else:
                # If sync result, wrap in coroutine and create task with proper closure
                # Use partial to capture result by value and avoid closure bug
                async def make_awaitable_wrapper(captured_result):
                    return captured_result

                task = asyncio.create_task(make_awaitable_wrapper(result))
            all_tasks.append(task)
            tool_name_mapping[id(task)] = tool_name

        # THREAD tools: run in thread pool
        for tool_name, (tool, tool_params) in thread_tools.items():
            # Check if thread tool has async use method (this is a bug in the tool implementation)
            if asyncio.iscoroutinefunction(tool.use):
                current_time = time.perf_counter() - start_time
                log_structured(
            logger,
                    "error",
                    "Thread tool has async use method - this is incorrect",
                    correlation_id=correlation_id,
                    perf_time=current_time,
                    tool_name=tool_name,
                    execution_mode=tool.execution_mode.value,
                )
                raise ToolExecutionModeError(
                    tool_name,
                    "THREAD",
                    "Thread tools must have sync use methods but this tool has async use method",
                    correlation_id=correlation_id
                )
            
            # Use functools.partial to properly capture variables and avoid closure issues
            thread_future: asyncio.Future[Any] = loop.run_in_executor(
                None, functools.partial(tool.use, tool_params, precallables)
            )
            all_tasks.append(thread_future)
            tool_name_mapping[id(thread_future)] = tool_name

        # PROCESS tools: run in process pool to bypass GIL
        # First, resolve required precallable results for process tools (they need resolved data, not futures)
        picklable_precallables = None
        if process_tools and precall_awaitables:
            # Determine which precallables are actually needed by process tools
            required_precallables = set()
            for tool_name, (tool, tool_params) in process_tools.items():
                # Check if LLM specified requirements in build plan (dynamic optimization)
                llm_required = tool_params.get('_required_precallables', None)
                tool_required = tool.required_precallables
                
                if llm_required is not None:  # LLM specified requirements (highest priority)
                    if isinstance(llm_required, list):
                        required_precallables.update(llm_required)
                        current_time = time.perf_counter() - start_time
                        log_structured(
            logger,
                            "info",
                            f"Process tool '{tool_name}' requirements set by LLM",
                            correlation_id=correlation_id,
                            perf_time=current_time,
                            llm_required_precallables=llm_required,
                        )
                    else:
                        current_time = time.perf_counter() - start_time
                        log_structured(
            logger,
                            "warning",
                            f"Process tool '{tool_name}' has invalid _required_precallables from LLM (not a list)",
                            correlation_id=correlation_id,
                            perf_time=current_time,
                            invalid_value=llm_required,
                        )
                        # Fall back to tool default
                        if tool_required:
                            required_precallables.update(tool_required)
                        else:
                            required_precallables.update(precall_awaitables.keys())
                elif tool_required:  # Tool-declared dependencies (fallback)
                    required_precallables.update(tool_required)
                    current_time = time.perf_counter() - start_time
                    log_structured(
            logger,
                        "info",
                        f"Process tool '{tool_name}' using tool-declared requirements",
                        correlation_id=correlation_id,
                        perf_time=current_time,
                        tool_required_precallables=tool_required,
                    )
                else:  # Empty list = require all precallables (backwards compatible)
                    required_precallables.update(precall_awaitables.keys())
                    current_time = time.perf_counter() - start_time
                    log_structured(
            logger,
                        "info",
                        f"Process tool '{tool_name}' requires all precallables (default behavior)",
                        correlation_id=correlation_id,
                        perf_time=current_time,
                        all_precallables=list(precall_awaitables.keys()),
                    )
            
            current_time = time.perf_counter() - start_time
            log_structured(
            logger,
                "info",
                "Resolving required precallable results for process tools",
                correlation_id=correlation_id,
                perf_time=current_time,
                required_count=len(required_precallables),
                available_count=len(precall_awaitables),
            )
            
            # Await only the required precallable results
            resolved_results = {}
            for precallable_name in required_precallables:
                if precallable_name in precall_awaitables:
                    try:
                        awaitable = precall_awaitables[precallable_name]
                        result = await awaitable
                        resolved_results[precallable_name] = result
                        current_time = time.perf_counter() - start_time
                        log_structured(
            logger,
                            "debug",
                            f"Resolved required precallable: {precallable_name}",
                            correlation_id=correlation_id,
                            perf_time=current_time,
                        )
                    except Exception as e:
                        current_time = time.perf_counter() - start_time
                        log_structured(
            logger,
                            "warning",
                            "Failed to resolve required precallable result",
                            correlation_id=correlation_id,
                            perf_time=current_time,
                            precallable_tool=precallable_name,
                            error=str(e),
                        )
                else:
                    current_time = time.perf_counter() - start_time
                    log_structured(
            logger,
                        "warning",
                        f"Required precallable '{precallable_name}' not found in available precallables",
                        correlation_id=correlation_id,
                        perf_time=current_time,
                        available_precallables=list(precall_awaitables.keys()),
                    )
            
            # Create picklable proxy with resolved results
            picklable_precallables = PicklablePrecallableResults(resolved_results)
            
            current_time = time.perf_counter() - start_time
            log_structured(
            logger,
                "info",
                "Created picklable precallables for process tools",
                correlation_id=correlation_id,
                perf_time=current_time,
                resolved_count=len(resolved_results),
                optimization_active=len(resolved_results) < len(precall_awaitables),
            )
        
        for tool_name, (tool, tool_params) in process_tools.items():
            # Check if process tool has async use method (this is a bug in the tool implementation)
            if asyncio.iscoroutinefunction(tool.use):
                current_time = time.perf_counter() - start_time
                log_structured(
            logger,
                    "error",
                    "Process tool has async use method - this is incorrect",
                    correlation_id=correlation_id,
                    perf_time=current_time,
                    tool_name=tool_name,
                    execution_mode=tool.execution_mode.value,
                )
                raise ToolExecutionModeError(
                    tool_name,
                    "PROCESS", 
                    "Process tools must have sync use methods but this tool has async use method",
                    correlation_id=correlation_id
                )
            
            # Ensure we have a process executor
            if request_state.process_executor is None:
                request_state.process_executor = ProcessPoolExecutor(max_workers=self.max_process_workers)
            # Best-effort: learn worker PIDs so we can safely terminate only our pool if required
            await self._ensure_process_worker_pids_initialized(request_state, loop)
            
            # Filter out internal parameters before passing to tool
            clean_tool_params = {k: v for k, v in tool_params.items() if not k.startswith('_')}
            

            # Use module-level helper function with resolved precallable results
            process_future: asyncio.Future[Any] = loop.run_in_executor(
                request_state.process_executor, functools.partial(_run_tool_for_process, tool, clean_tool_params, picklable_precallables)
            )
            all_tasks.append(process_future)
            tool_name_mapping[id(process_future)] = tool_name

        # Wait for all tools to complete
        stage_results: Dict[str, Any] = {}
        if all_tasks:
            # mypy has trouble with Union[Awaitable, Future] in gather, use type ignore
            results = await asyncio.gather(*all_tasks, return_exceptions=True)  # type: ignore
            for task, result in zip(all_tasks, results):  # type: ignore[assignment]
                tool_name = tool_name_mapping[id(task)]
                if isinstance(result, Exception):
                    current_time = time.perf_counter() - start_time
                    log_structured(
            logger,
                        "error",
                        "Tool execution failed",
                        correlation_id=correlation_id,
                        perf_time=current_time,
                        tool_name=tool_name,
                        stage_name=stage_name,
                        error=str(result),
                        error_type=type(result).__name__,
                    )
                    raise ToolExecutionError(
                        tool_name,
                        stage_name,
                        result,
                        correlation_id=correlation_id
                    )
                else:
                    stage_results[tool_name] = result if result is not None else {}
                    current_time = time.perf_counter() - start_time
                    log_structured(
            logger,
                        "debug",
                        "Tool completed successfully",
                        correlation_id=correlation_id,
                        perf_time=current_time,
                        tool_name=tool_name,
                        stage_name=stage_name,
                    )
        return stage_results

    def _resolve_references(
        self,
        params: Dict[str, Any],
        stage_outputs: Dict[str, Dict[str, Any]],
        current_stage_num: Optional[int] = None,
        correlation_id: Optional[str] = None,
        start_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Resolves all $ref.stage.tool.output references in parameters with optional stage validation.
        Uses recursive structure traversal instead of regex-over-JSON for robustness.

        Args:
            params: The parameters to resolve references in.
            stage_outputs: The outputs of the previous stages.
            current_stage_num: Optional current stage number for validation when processing stages.
            correlation_id: Optional unique identifier for this request.
            start_time: Optional start time of the generate_response call.

        Returns:
            Dict[str, Any]: The parameters with references resolved.
        """
        ref_count = 0

        def resolve_value(value: Any) -> Any:
            nonlocal ref_count
            
            if isinstance(value, str) and value.startswith("$ref."):
                # Full reference replacement
                ref_path = value[5:]  # Remove "$ref." prefix
                parts = ref_path.split(".")
                if len(parts) != 3:
                    raise InvalidReferencePathError(
                        ref_path,
                        correlation_id=correlation_id
                    )
                
                stage_name, tool_name, output_param = parts
                
                # Stage validation
                if current_stage_num is not None:
                    try:
                        referenced_stage_num = int(stage_name.split("_")[1])
                        if referenced_stage_num >= current_stage_num:
                            raise StageValidationError(
                                ref_path,
                                current_stage_num,
                                referenced_stage_num,
                                correlation_id=correlation_id
                            )
                    except (ValueError, IndexError) as e:
                        raise InvalidReferencePathError(
                            ref_path,
                            correlation_id=correlation_id
                        ) from e
                
                # Resolve the reference - distinguish between missing values and legitimate None
                stage_data = stage_outputs.get(stage_name, {})
                tool_data = stage_data.get(tool_name, {})
                
                if output_param not in tool_data:
                    raise ReferenceResolutionError(
                        ref_path,
                        "Reference could not be resolved - output parameter not found",
                        correlation_id=correlation_id
                    )
                
                resolved_value = tool_data[output_param]
                # None is a valid value that should be preserved (converted to JSON null)
                
                ref_count += 1
                current_perf_time = (
                    time.perf_counter() - start_time if start_time is not None else None
                )
                log_structured(
                    logger,
                    "debug",
                    "Resolved reference",
                    correlation_id=correlation_id,
                    perf_time=current_perf_time,
                    ref_path=ref_path,
                    resolved_type=type(resolved_value).__name__,
                )
                return resolved_value
                
            elif isinstance(value, str) and "$ref." in value:
                # Embedded reference in string - handle multiple refs
                result = value
                import re
                for match in re.finditer(r'\$ref\.([\w\.]+)', value):
                    ref_path = match.group(1)
                    parts = ref_path.split(".")
                    if len(parts) != 3:
                        raise InvalidReferencePathError(
                            ref_path,
                            correlation_id=correlation_id
                        )
                    
                    stage_name, tool_name, output_param = parts
                    
                    # Stage validation
                    if current_stage_num is not None:
                        try:
                            referenced_stage_num = int(stage_name.split("_")[1])
                            if referenced_stage_num >= current_stage_num:
                                raise StageValidationError(
                                    ref_path,
                                    current_stage_num,
                                    referenced_stage_num,
                                    correlation_id=correlation_id
                                )
                        except (ValueError, IndexError) as e:
                            raise InvalidReferencePathError(
                                ref_path,
                                correlation_id=correlation_id
                            ) from e
                    
                    # Resolve the reference - distinguish between missing values and legitimate None
                    stage_data = stage_outputs.get(stage_name, {})
                    tool_data = stage_data.get(tool_name, {})
                    
                    if output_param not in tool_data:
                        raise ReferenceResolutionError(
                            ref_path,
                            "Reference could not be resolved - output parameter not found",
                            correlation_id=correlation_id
                        )
                    
                    resolved_value = tool_data[output_param]
                    # None is a valid value that should be preserved
                    
                    ref_count += 1
                    # Replace the reference in the string
                    result = result.replace(f"$ref.{ref_path}", str(resolved_value))
                    
                return result
                
            elif isinstance(value, dict):
                # Recursively resolve dictionary values
                return {k: resolve_value(v) for k, v in value.items()}
                
            elif isinstance(value, list):
                # Recursively resolve list items
                return [resolve_value(item) for item in value]
                
            else:
                # Return unchanged for non-reference values
                return value

        try:
            resolved_params = resolve_value(params)
            if ref_count > 0:
                current_perf_time = (
                    time.perf_counter() - start_time if start_time is not None else None
                )
                log_structured(
                    logger,
                    "debug",
                    "Resolved references in parameters",
                    correlation_id=correlation_id,
                    perf_time=current_perf_time,
                    ref_count=ref_count,
                )
            return resolved_params
        except Exception as e:
            if isinstance(e, (InvalidReferencePathError, StageValidationError, ReferenceResolutionError)):
                raise  # Re-raise our custom exceptions
            
            # Wrap unexpected errors
            current_perf_time = (
                time.perf_counter() - start_time if start_time is not None else None
            )
            log_structured(
                logger,
                "error",
                "Unexpected error resolving references",
                correlation_id=correlation_id,
                perf_time=current_perf_time,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ReferenceResolutionError(
                "unknown",
                f"Unexpected error resolving references: {e}",
                correlation_id=correlation_id,
                original_error=str(e),
                original_error_type=type(e).__name__
            ) from e

    async def generate_response(
        self,
        customer_request: str,
        conversation_history: Any,
        additional_context_prompt: str,
        max_attempts: int = 3,
        hedge_requests: int = 2,
    ) -> Tuple[List[Blueprint], str, Dict[str, Dict[str, Any]], Dict[str, Any]]:
        """
        Generates a response to the customer's request given the conversation history and context. The function will generate a build plan describing the tool call order to be used to fill in all selected blueprints, execute it, and return the filled blueprints to the caller.

        Args:
            customer_request (str): The customer's current request.

            conversation_history (Any): The conversation history with the customer. The format of the conversation history does not have to precisely match what is generally expected by the LLM because the history is passed within the user prompt. Generally something like List[Dict[str, str]] works well.

            additional_context_prompt (str): Any additional global instructions that should be followed when generating the build plan. This can contain instructions or notes about the customer.

            max_attempts (int): The maximum number of attempts to generate a response.

        Returns:
            Tuple[List[Blueprint], str, Dict[str, Dict[str, Any]], Dict[str, Any]]: A tuple containing:
                - The list of blueprints chosen by the model after having been filled by the Architect
                - The original build plan as a JSON string
                - The stage outputs dictionary containing all tool execution results
                - The surviving precallable tools (those not killed after response)
        """
        correlation_id = str(uuid.uuid4())
        start_time = time.perf_counter()
        log_structured(
            logger,
            "warning",
            "Starting generate_response",
            correlation_id=correlation_id,
            perf_time=0.0,
            request_preview=customer_request[:100],
            request_length=len(customer_request),
        )

        # Create per-request state for thread-safety
        request_state = RequestState(self.max_process_workers)
        
        try:
            # Start precallables once, outside retry loop for true parallel execution
            precall_awaitables: Dict[
                str, Union[asyncio.Task[Any], asyncio.Future[Any]]
            ] = self._start_precall_tools(request_state, correlation_id, start_time)
            
            # Yield control briefly so async tasks can start running immediately alongside thread tasks
            await asyncio.sleep(0)
            
            current_time = time.perf_counter() - start_time
            log_structured(
                logger,
                "warning",
                "Precallable tools started and running in background",
                correlation_id=correlation_id,
                perf_time=current_time,
                precallable_count=len(precall_awaitables),
            )

            error_message: Optional[str] = None
            for attempt in range(max_attempts):
                build_plan: Optional[str] = None
                try:
                    build_plan_start = time.perf_counter()
                    build_plan = await self._generate_build_plan(
                        customer_request,
                        conversation_history,
                        additional_context_prompt,
                        correlation_id,
                        start_time,
                        previous_attempt_error_message=error_message,
                        hedge_requests=hedge_requests,
                    )
                    build_plan_time = time.perf_counter() - build_plan_start
                    elapsed_total = time.perf_counter() - start_time
                    log_structured(
                logger,
                        "warning",
                        "Build plan generated",
                        correlation_id=correlation_id,
                        perf_time=elapsed_total,
                        generation_time_s=round(build_plan_time, 2),
                        total_elapsed_s=round(elapsed_total, 2),
                    )

                    execution_start = time.perf_counter()
                    filled_blueprints, stage_outputs = await self._execute_build_plan(
                        request_state, build_plan, precall_awaitables, correlation_id, start_time
                    )
                    execution_time = time.perf_counter() - execution_start
                    total_time = time.perf_counter() - start_time
                    log_structured(
                logger,
                        "warning",
                        "Build plan executed",
                        correlation_id=correlation_id,
                        perf_time=total_time,
                        execution_time_s=round(execution_time, 2),
                        total_time_s=round(total_time, 2),
                    )

                    # Clean up precallables immediately after build plan execution
                    surviving_tools = await self._cleanup_precallables(request_state, correlation_id, start_time)
                    
                    return filled_blueprints, build_plan, stage_outputs, surviving_tools
                except Exception as e:
                    elapsed_total = time.perf_counter() - start_time
                    log_structured(
                logger,
                        "error",
                        "Failed to generate build plan",
                        correlation_id=correlation_id,
                        perf_time=elapsed_total,
                        elapsed_time_s=round(elapsed_total, 2),
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    if build_plan:
                        log_structured(
                logger,
                            "warning",
                            "Build plan content for debugging",
                            correlation_id=correlation_id,
                            perf_time=elapsed_total,
                            build_plan_preview=build_plan[:500] if build_plan else None,
                            build_plan_length=len(build_plan) if build_plan else 0,
                        )
                    error_message = str(e)
                    if attempt < max_attempts - 1:
                        sleep_duration = min(0.25 * (2**attempt), 10)
                        log_structured(
                logger,
                            "warning",
                            "Retrying build plan generation",
                            correlation_id=correlation_id,
                            perf_time=elapsed_total,
                            sleep_duration_s=sleep_duration,
                            current_attempt=attempt + 1,
                            max_attempts=max_attempts,
                            elapsed_time_s=round(elapsed_total, 2),
                        )
                        await asyncio.sleep(sleep_duration)
            total_time = time.perf_counter() - start_time
            log_structured(
                logger,
                "error",
                "Failed to generate build plan after max attempts",
                correlation_id=correlation_id,
                perf_time=total_time,
                max_attempts=max_attempts,
                total_time_s=round(total_time, 2),
            )
            raise BuildPlanGenerationError(
                max_attempts,
                correlation_id=correlation_id
            )
        finally:
            # Ensure cleanup always happens, even on failure
            if not request_state.cleanup_performed:
                try:
                    await self._cleanup_precallables(request_state, correlation_id, start_time)
                except Exception as cleanup_error:
                    log_structured(
                        logger,
                        "error",
                        "Error during cleanup in finally block",
                        correlation_id=correlation_id,
                        perf_time=time.perf_counter() - start_time,
                        error=str(cleanup_error),
                        error_type=type(cleanup_error).__name__,
                    )

    async def _cleanup_precallables(self, request_state: RequestState, correlation_id: str, start_time: float) -> Dict[str, Any]:
        """
        Clean up precallable tools based on their kill_after_response setting.
        Returns a dict of surviving (non-killed) tool results.
        """
        if request_state.cleanup_performed:
            return {}  # Already cleaned up
            
        request_state.cleanup_performed = True
        surviving_tools: Dict[str, Any] = {}
        killed_count = 0
        killed_process_tools = []
        
        for tool_name, tool_state in list(request_state.running_precallables.items()):
            current_time = time.perf_counter() - start_time
            
            # Check if we should kill this tool
            should_kill = tool_state.tool.kill_after_response
            
            if should_kill:
                log_structured(
            logger,
                    "info",
                    "Killing precallable tool after response",
                    correlation_id=correlation_id,
                    perf_time=current_time,
                    tool_name=tool_name,
                    execution_mode=tool_state.tool.execution_mode.value,
                )
                
                # Kill based on execution mode
                if tool_state.tool.execution_mode == ExecutionMode.ASYNC:
                    # Cancel async task
                    if not tool_state.awaitable.done():
                        tool_state.awaitable.cancel()
                        try:
                            await tool_state.awaitable
                        except asyncio.CancelledError:
                            pass  # Expected
                
                elif tool_state.tool.execution_mode == ExecutionMode.THREAD:
                    # Thread futures can't be cleanly cancelled, but we can ignore the result
                    pass  # Let it complete naturally
                
                elif tool_state.tool.execution_mode == ExecutionMode.PROCESS:
                    # For process tools, try to kill more aggressively
                    if not tool_state.awaitable.done():
                        # Try to cancel the future first
                        cancelled = tool_state.awaitable.cancel()
                        
                        # Try to get the process ID and kill it directly (if available)
                        pid_killed = False
                        try:
                            # Try to access the underlying process if possible
                            if hasattr(tool_state.awaitable, '_state') and hasattr(tool_state.awaitable._state, 'running_task'):
                                # This is a long shot, but try to find the process
                                pass
                        except Exception:
                            pass
                        
                        current_time = time.perf_counter() - start_time
                        log_structured(
            logger,
                            "info",
                            f"Cancelled process future: {cancelled}, PID killed: {pid_killed}",
                            correlation_id=correlation_id,
                            perf_time=current_time,
                            tool_name=tool_name,
                        )
                    killed_process_tools.append(tool_name)
                
                tool_state.is_killed = True
                killed_count += 1
                # Remove from running list
                del request_state.running_precallables[tool_name]
                
            else:
                # Keep alive - get the result if completed, or placeholder if still running
                if not tool_state.is_completed:
                    try:
                        # Try to get result without blocking too long
                        if tool_state.awaitable.done():
                            tool_state.result = tool_state.awaitable.result()
                            tool_state.is_completed = True
                            surviving_tools[tool_name] = tool_state.result
                        else:
                            # Tool is still running, keep it for next time and add to surviving tools
                            log_structured(
            logger,
                                "info",
                                "Keeping precallable tool alive for reuse",
                                correlation_id=correlation_id,
                                perf_time=current_time,
                                tool_name=tool_name,
                                execution_mode=tool_state.tool.execution_mode.value,
                            )
                            # Add to surviving tools even if still running
                            surviving_tools[tool_name] = {
                                "status": "running",
                                "tool": tool_state.tool,
                                "awaitable": tool_state.awaitable
                            }
                    except Exception as e:
                        log_structured(
            logger,
                            "warning",
                            "Error getting result from surviving tool",
                            correlation_id=correlation_id,
                            perf_time=current_time,
                            tool_name=tool_name,
                            error=str(e),
                        )
                else:
                    surviving_tools[tool_name] = tool_state.result
        
        # If we killed any process tools, shutdown the process executor deterministically
        if killed_process_tools and request_state.process_executor is not None:
            current_time = time.perf_counter() - start_time
            log_structured(
                logger,
                "warning",
                "Shutting down ProcessPoolExecutor for killed process tools",
                correlation_id=correlation_id,
                perf_time=current_time,
                killed_process_tools=killed_process_tools,
            )
            
            # Step 1: Try graceful shutdown first
            graceful_success = False
            try:
                # Use graceful shutdown with cancellation
                request_state.process_executor.shutdown(wait=True, cancel_futures=True)
                graceful_success = True
                
                current_time = time.perf_counter() - start_time
                log_structured(
                    logger,
                    "info",
                    "ProcessPoolExecutor graceful shutdown complete",
                    correlation_id=correlation_id,
                    perf_time=current_time,
                )
            except Exception as e:
                current_time = time.perf_counter() - start_time
                log_structured(
                    logger,
                    "warning",
                    "ProcessPoolExecutor graceful shutdown failed",
                    correlation_id=correlation_id,
                    perf_time=current_time,
                    error=str(e),
                )
            
            # Step 2: If graceful shutdown failed, terminate workers directly using collected PIDs
            if not graceful_success and request_state.process_worker_pids:
                current_time = time.perf_counter() - start_time
                log_structured(
                    logger,
                    "warning",
                    "Attempting deterministic worker termination using collected PIDs",
                    correlation_id=correlation_id,
                    perf_time=current_time,
                    pid_count=len(request_state.process_worker_pids),
                )
                killed_worker_count = 0
                for pid in list(request_state.process_worker_pids):
                    try:
                        killtree(pid, including_parent=True)
                        killed_worker_count += 1
                        log_structured(
                            logger,
                            "info",
                            f"Successfully terminated worker process {pid}",
                            correlation_id=correlation_id,
                            perf_time=current_time,
                            pid=pid,
                        )
                    except Exception as pid_error:
                        log_structured(
                            logger,
                            "warning",
                            f"Error killing worker process {pid}",
                            correlation_id=correlation_id,
                            perf_time=current_time,
                            pid=pid,
                            error=str(pid_error),
                        )
                
                current_time = time.perf_counter() - start_time
                log_structured(
                    logger,
                    "info",
                    "Completed deterministic worker termination",
                    correlation_id=correlation_id,
                    perf_time=current_time,
                    killed_workers=killed_worker_count,
                    total_workers=len(request_state.process_worker_pids),
                )
            
            # Clean up state
            request_state.process_executor = None  # Will be recreated if needed later
            request_state.process_worker_pids.clear()
        
        current_time = time.perf_counter() - start_time
        log_structured(
            logger,
            "info",
            "Completed precallable tool cleanup",
            correlation_id=correlation_id,
            perf_time=current_time,
            killed_count=killed_count,
            surviving_count=len(surviving_tools),
            executor_shutdown=len(killed_process_tools) > 0,
        )
        
        return surviving_tools

    def cleanup(self):
        """
        Clean up global resources. 
        Note: Per-request cleanup is now handled automatically in generate_response.
        This method is kept for backwards compatibility but is largely unnecessary.
        """
        log_structured(
            logger,
            "warning",
            "Cleanup called - per-request cleanup is now automatic",
            component="architect",
        )
