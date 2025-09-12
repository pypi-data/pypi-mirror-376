"""
Connection management for pipelines.
"""

import asyncio
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from .base import BasePipeline, PipelineError, PipelineExecutionError


class ConnectionType(Enum):
    """Types of pipeline connections."""
    SEQUENTIAL = "sequential"  # Data flows from one pipeline to the next
    PARALLEL = "parallel"     # Data is processed by multiple pipelines concurrently
    CONDITIONAL = "conditional"  # Data flows based on conditions
    MERGE = "merge"           # Multiple pipeline outputs are merged


class PipelineConnection:
    """Represents a connection between two pipelines."""
    
    def __init__(
        self,
        source: BasePipeline,
        target: BasePipeline,
        connection_type: ConnectionType = ConnectionType.SEQUENTIAL,
        condition_func: Optional[Callable] = None,
        merge_func: Optional[Callable] = None
    ):
        """
        Initialize a pipeline connection.
        
        Args:
            source: Source pipeline
            target: Target pipeline
            connection_type: Type of connection
            condition_func: Function to evaluate for conditional connections
            merge_func: Function to merge data for merge connections
        """
        self.id = uuid4().hex
        self.source = source
        self.target = target
        self.connection_type = connection_type
        self.condition_func = condition_func
        self.merge_func = merge_func
        
        # Add connection to source pipeline
        source.add_connection(target)
    
    async def can_execute(self, data: Any) -> bool:
        """Check if this connection can be executed with given data."""
        if self.connection_type == ConnectionType.CONDITIONAL and self.condition_func:
            try:
                return await self._safe_call(self.condition_func, data)
            except Exception:
                return False
        return True
    
    async def _safe_call(self, func: Callable, *args, **kwargs) -> Any:
        """Safely call a function, handling both sync and async functions."""
        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as e:
            raise PipelineExecutionError(f"Function call failed: {e}")
    
    def __repr__(self) -> str:
        return (
            f"<PipelineConnection(id='{self.id}', "
            f"source='{self.source.config.name}', "
            f"target='{self.target.config.name}', "
            f"type='{self.connection_type.value}')>"
        )


class PipelineConnector:
    """
    Manages connections between pipelines and coordinates data flow.
    """
    
    def __init__(self):
        """Initialize the pipeline connector."""
        self.connections: Dict[str, PipelineConnection] = {}
        self._graph: Dict[str, List[str]] = {}  # Adjacency list for topology
        
    def connect(
        self,
        source: BasePipeline,
        target: BasePipeline,
        connection_type: ConnectionType = ConnectionType.SEQUENTIAL,
        condition_func: Optional[Callable] = None,
        merge_func: Optional[Callable] = None
    ) -> str:
        """
        Connect two pipelines.
        
        Args:
            source: Source pipeline
            target: Target pipeline
            connection_type: Type of connection
            condition_func: Function for conditional connections
            merge_func: Function for merge connections
            
        Returns:
            Connection ID
            
        Raises:
            PipelineError: If connection cannot be established
        """
        # Check for circular dependencies
        if self._would_create_cycle(source.id, target.id):
            raise PipelineError(
                f"Cannot connect {source.config.name} to {target.config.name}: "
                "would create a circular dependency"
            )
        
        connection = PipelineConnection(
            source=source,
            target=target,
            connection_type=connection_type,
            condition_func=condition_func,
            merge_func=merge_func
        )
        
        self.connections[connection.id] = connection
        
        # Update graph
        if source.id not in self._graph:
            self._graph[source.id] = []
        self._graph[source.id].append(target.id)
        
        return connection.id
    
    def disconnect(self, connection_id: str) -> bool:
        """
        Disconnect pipelines by connection ID.
        
        Args:
            connection_id: ID of the connection to remove
            
        Returns:
            True if disconnection was successful
        """
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        
        # Remove from source pipeline
        connection.source.remove_connection(connection.target)
        
        # Update graph
        if connection.source.id in self._graph:
            if connection.target.id in self._graph[connection.source.id]:
                self._graph[connection.source.id].remove(connection.target.id)
            
            # Clean up empty entries
            if not self._graph[connection.source.id]:
                del self._graph[connection.source.id]
        
        # Remove connection
        del self.connections[connection_id]
        
        return True
    
    def get_connections(self) -> List[PipelineConnection]:
        """Get all pipeline connections."""
        return list(self.connections.values())
    
    def get_connections_for_pipeline(self, pipeline: BasePipeline) -> List[PipelineConnection]:
        """Get all connections where the pipeline is the source."""
        return [
            conn for conn in self.connections.values()
            if conn.source.id == pipeline.id
        ]
    
    def get_execution_order(self) -> List[List[str]]:
        """
        Get the execution order for pipelines using topological sorting.
        
        Returns:
            List of lists, where each inner list contains pipeline IDs that can run in parallel
        """
        return self._topological_sort()
    
    def _would_create_cycle(self, source_id: str, target_id: str) -> bool:
        """Check if adding a connection would create a cycle."""
        # If target can reach source, adding source->target would create a cycle
        return self._can_reach(target_id, source_id)
    
    def _can_reach(self, start_id: str, target_id: str) -> bool:
        """Check if start_id can reach target_id in the current graph."""
        if start_id == target_id:
            return True
        
        visited = set()
        stack = [start_id]
        
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == target_id:
                return True
            
            if current in self._graph:
                stack.extend(self._graph[current])
        
        return False
    
    def _topological_sort(self) -> List[List[str]]:
        """
        Perform topological sorting to determine execution order.
        
        Returns:
            List of execution levels (each level can be executed in parallel)
        """
        # Calculate in-degrees
        in_degree = {}
        all_nodes = set()
        
        for source_id, targets in self._graph.items():
            all_nodes.add(source_id)
            if source_id not in in_degree:
                in_degree[source_id] = 0
            
            for target_id in targets:
                all_nodes.add(target_id)
                in_degree[target_id] = in_degree.get(target_id, 0) + 1
        
        # Nodes with no incoming edges
        queue = [node for node in all_nodes if in_degree.get(node, 0) == 0]
        execution_levels = []
        
        while queue:
            current_level = queue.copy()
            queue = []
            execution_levels.append(current_level)
            
            for node in current_level:
                if node in self._graph:
                    for neighbor in self._graph[node]:
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            queue.append(neighbor)
        
        return execution_levels