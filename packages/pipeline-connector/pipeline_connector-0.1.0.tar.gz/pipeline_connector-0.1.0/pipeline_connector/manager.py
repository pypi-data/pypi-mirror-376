"""
Pipeline manager for orchestrating multiple connected pipelines.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

from .base import BasePipeline, PipelineError, PipelineExecutionError, PipelineStatus
from .connectors import PipelineConnector, ConnectionType, PipelineConnection


class PipelineManager:
    """
    Main manager class for orchestrating multiple connected pipelines.
    
    This class provides high-level functionality for:
    - Managing pipeline connections
    - Executing pipeline chains
    - Handling parallel execution
    - Managing execution state
    - Error handling and recovery
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the pipeline manager.
        
        Args:
            name: Optional name for the manager
        """
        self.name = name or f"manager_{uuid4().hex[:8]}"
        self.connector = PipelineConnector()
        self.pipelines: Dict[str, BasePipeline] = {}
        self.logger = self._setup_logger()
        self._execution_state: Dict[str, Any] = {}
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the manager."""
        logger = logging.getLogger(f"pipeline_connector.manager.{self.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def add_pipeline(self, pipeline: BasePipeline) -> str:
        """
        Add a pipeline to the manager.
        
        Args:
            pipeline: Pipeline to add
            
        Returns:
            Pipeline ID
        """
        self.pipelines[pipeline.id] = pipeline
        self.logger.info(f"Added pipeline: {pipeline.config.name} (ID: {pipeline.id})")
        return pipeline.id
    
    def remove_pipeline(self, pipeline_id: str) -> bool:
        """
        Remove a pipeline from the manager.
        
        Args:
            pipeline_id: ID of pipeline to remove
            
        Returns:
            True if pipeline was removed
        """
        if pipeline_id in self.pipelines:
            pipeline = self.pipelines[pipeline_id]
            
            # Remove all connections involving this pipeline
            connections_to_remove = []
            for conn in self.connector.get_connections():
                if conn.source.id == pipeline_id or conn.target.id == pipeline_id:
                    connections_to_remove.append(conn.id)
            
            for conn_id in connections_to_remove:
                self.connector.disconnect(conn_id)
            
            del self.pipelines[pipeline_id]
            self.logger.info(f"Removed pipeline: {pipeline.config.name} (ID: {pipeline_id})")
            return True
        
        return False
    
    def connect(
        self,
        source: Union[BasePipeline, str],
        target: Union[BasePipeline, str],
        connection_type: ConnectionType = ConnectionType.SEQUENTIAL,
        **kwargs
    ) -> str:
        """
        Connect two pipelines.
        
        Args:
            source: Source pipeline or pipeline ID
            target: Target pipeline or pipeline ID
            connection_type: Type of connection
            **kwargs: Additional connection parameters
            
        Returns:
            Connection ID
            
        Raises:
            PipelineError: If connection cannot be established
        """
        source_pipeline = self._get_pipeline(source)
        target_pipeline = self._get_pipeline(target)
        
        # Ensure both pipelines are managed by this manager
        if source_pipeline.id not in self.pipelines:
            self.add_pipeline(source_pipeline)
        if target_pipeline.id not in self.pipelines:
            self.add_pipeline(target_pipeline)
        
        connection_id = self.connector.connect(
            source_pipeline,
            target_pipeline,
            connection_type,
            **kwargs
        )
        
        self.logger.info(
            f"Connected {source_pipeline.config.name} -> {target_pipeline.config.name} "
            f"(Type: {connection_type.value}, ID: {connection_id})"
        )
        
        return connection_id
    
    def disconnect(self, connection_id: str) -> bool:
        """
        Disconnect pipelines by connection ID.
        
        Args:
            connection_id: ID of connection to remove
            
        Returns:
            True if disconnection was successful
        """
        success = self.connector.disconnect(connection_id)
        if success:
            self.logger.info(f"Disconnected connection: {connection_id}")
        return success
    
    async def execute(
        self,
        data: Any,
        start_pipeline: Optional[Union[BasePipeline, str]] = None,
        **kwargs
    ) -> Any:
        """
        Execute the pipeline chain with input data.
        
        Args:
            data: Input data to process
            start_pipeline: Optional starting pipeline (if None, finds root pipelines)
            **kwargs: Additional execution parameters
            
        Returns:
            Final processed data
            
        Raises:
            PipelineExecutionError: If execution fails
        """
        self.logger.info(f"Starting pipeline execution with manager: {self.name}")
        
        try:
            if start_pipeline:
                # Execute from specific pipeline
                pipeline = self._get_pipeline(start_pipeline)
                return await self._execute_single_chain(pipeline, data, **kwargs)
            else:
                # Execute all pipeline chains
                return await self._execute_all_chains(data, **kwargs)
                
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            raise PipelineExecutionError(f"Manager execution failed: {e}") from e
    
    async def _execute_all_chains(self, data: Any, **kwargs) -> List[Any]:
        """Execute all pipeline chains starting from root pipelines."""
        execution_levels = self.connector.get_execution_order()
        
        if not execution_levels:
            self.logger.warning("No pipelines to execute")
            return [data]
        
        results = []
        current_data = data
        
        for level in execution_levels:
            level_results = []
            
            # Execute pipelines in current level concurrently
            tasks = []
            for pipeline_id in level:
                if pipeline_id in self.pipelines:
                    pipeline = self.pipelines[pipeline_id]
                    task = self._execute_pipeline_with_tracking(pipeline, current_data, **kwargs)
                    tasks.append(task)
            
            if tasks:
                level_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check for exceptions
                for i, result in enumerate(level_results):
                    if isinstance(result, Exception):
                        pipeline_id = level[i]
                        pipeline = self.pipelines[pipeline_id]
                        self.logger.error(f"Pipeline {pipeline.config.name} failed: {result}")
                        raise PipelineExecutionError(f"Pipeline execution failed: {result}")
                
                # Use results as input for next level
                if len(level_results) == 1:
                    current_data = level_results[0]
                else:
                    current_data = level_results
                
                results.extend(level_results)
        
        return results if len(results) > 1 else (results[0] if results else data)
    
    async def _execute_single_chain(
        self,
        start_pipeline: BasePipeline,
        data: Any,
        **kwargs
    ) -> Any:
        """Execute a single pipeline chain starting from the given pipeline."""
        current_data = data
        visited = set()
        
        async def execute_recursive(pipeline: BasePipeline, input_data: Any) -> Any:
            if pipeline.id in visited:
                self.logger.warning(f"Circular reference detected for pipeline: {pipeline.config.name}")
                return input_data
            
            visited.add(pipeline.id)
            
            # Execute current pipeline
            result = await self._execute_pipeline_with_tracking(pipeline, input_data, **kwargs)
            
            # Get connections for this pipeline
            connections = self.connector.get_connections_for_pipeline(pipeline)
            
            if not connections:
                # End of chain
                return result
            
            # Execute connected pipelines
            final_results = []
            for connection in connections:
                if await connection.can_execute(result):
                    next_result = await execute_recursive(connection.target, result)
                    final_results.append(next_result)
            
            return final_results[0] if len(final_results) == 1 else final_results
        
        return await execute_recursive(start_pipeline, current_data)
    
    async def _execute_pipeline_with_tracking(
        self,
        pipeline: BasePipeline,
        data: Any,
        **kwargs
    ) -> Any:
        """Execute a pipeline with state tracking."""
        pipeline_id = pipeline.id
        
        # Update execution state
        self._execution_state[pipeline_id] = {
            'status': PipelineStatus.RUNNING,
            'start_time': asyncio.get_event_loop().time()
        }
        
        try:
            result = await pipeline.execute(data, **kwargs)
            
            self._execution_state[pipeline_id].update({
                'status': PipelineStatus.COMPLETED,
                'end_time': asyncio.get_event_loop().time(),
                'result': result
            })
            
            return result
            
        except Exception as e:
            self._execution_state[pipeline_id].update({
                'status': PipelineStatus.FAILED,
                'end_time': asyncio.get_event_loop().time(),
                'error': str(e)
            })
            raise
    
    def _get_pipeline(self, pipeline: Union[BasePipeline, str]) -> BasePipeline:
        """Get pipeline object from pipeline or ID."""
        if isinstance(pipeline, str):
            if pipeline not in self.pipelines:
                raise PipelineError(f"Pipeline not found: {pipeline}")
            return self.pipelines[pipeline]
        return pipeline
    
    def get_pipelines(self) -> List[BasePipeline]:
        """Get all managed pipelines."""
        return list(self.pipelines.values())
    
    def get_connections(self) -> List[PipelineConnection]:
        """Get all pipeline connections."""
        return self.connector.get_connections()
    
    def get_execution_state(self) -> Dict[str, Any]:
        """Get current execution state for all pipelines."""
        return self._execution_state.copy()
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get metrics for all managed pipelines."""
        metrics = {}
        for pipeline_id, pipeline in self.pipelines.items():
            metrics[pipeline_id] = {
                'config': pipeline.config.dict(),
                'metrics': pipeline.get_metrics().dict(),
                'connections': len(pipeline.get_connections())
            }
        return metrics
    
    def reset_execution_state(self) -> None:
        """Reset execution state for all pipelines."""
        self._execution_state.clear()
        self.logger.info("Reset execution state")
    
    def __repr__(self) -> str:
        return (
            f"<PipelineManager(name='{self.name}', "
            f"pipelines={len(self.pipelines)}, "
            f"connections={len(self.connector.get_connections())})>"
        )