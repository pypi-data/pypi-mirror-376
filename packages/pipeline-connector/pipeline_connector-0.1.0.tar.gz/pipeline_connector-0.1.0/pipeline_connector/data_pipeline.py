"""
Ready-to-use data pipeline implementations.
"""

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Union

from .base import BasePipeline, PipelineConfig, PipelineExecutionError


class DataPipeline(BasePipeline):
    """
    A ready-to-use pipeline implementation for common data processing tasks.
    
    This pipeline can handle various data transformation operations including:
    - Data filtering
    - Data transformation
    - Data aggregation
    - Data validation
    """
    
    def __init__(
        self,
        name: str,
        transform_func: Optional[Callable] = None,
        filter_func: Optional[Callable] = None,
        config: Optional[PipelineConfig] = None
    ):
        """
        Initialize the data pipeline.
        
        Args:
            name: Name of the pipeline
            transform_func: Function to transform data
            filter_func: Function to filter data
            config: Pipeline configuration
        """
        if config is None:
            config = PipelineConfig(name=name)
        else:
            config.name = name
            
        super().__init__(config)
        
        self.transform_func = transform_func
        self.filter_func = filter_func
    
    async def process(self, data: Any) -> Any:
        """
        Process the input data through filtering and transformation.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data
        """
        processed_data = data
        
        # Apply filter if provided
        if self.filter_func:
            if isinstance(processed_data, (list, tuple)):
                processed_data = [
                    item for item in processed_data 
                    if await self._safe_call(self.filter_func, item)
                ]
            else:
                if not await self._safe_call(self.filter_func, processed_data):
                    return None
        
        # Apply transformation if provided
        if self.transform_func:
            if isinstance(processed_data, (list, tuple)):
                processed_data = [
                    await self._safe_call(self.transform_func, item)
                    for item in processed_data
                ]
            else:
                processed_data = await self._safe_call(self.transform_func, processed_data)
        
        return processed_data
    
    async def _safe_call(self, func: Callable, *args, **kwargs) -> Any:
        """Safely call a function, handling both sync and async functions."""
        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as e:
            raise PipelineExecutionError(f"Function call failed: {e}", self.id) from e


class DataSourcePipeline(BasePipeline):
    """Pipeline for reading data from various sources."""
    
    def __init__(
        self,
        name: str,
        source_func: Callable,
        config: Optional[PipelineConfig] = None
    ):
        """
        Initialize the data source pipeline.
        
        Args:
            name: Name of the pipeline
            source_func: Function to read data from source
            config: Pipeline configuration
        """
        if config is None:
            config = PipelineConfig(name=name)
        else:
            config.name = name
            
        super().__init__(config)
        self.source_func = source_func
    
    async def process(self, data: Any = None) -> Any:
        """
        Read data from the configured source.
        
        Args:
            data: Optional input data (may be ignored by source)
            
        Returns:
            Data from the source
        """
        try:
            result = self.source_func(data) if data is not None else self.source_func()
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as e:
            raise PipelineExecutionError(f"Source read failed: {e}", self.id) from e


class DataSinkPipeline(BasePipeline):
    """Pipeline for writing data to various destinations."""
    
    def __init__(
        self,
        name: str,
        sink_func: Callable,
        config: Optional[PipelineConfig] = None
    ):
        """
        Initialize the data sink pipeline.
        
        Args:
            name: Name of the pipeline
            sink_func: Function to write data to destination
            config: Pipeline configuration
        """
        if config is None:
            config = PipelineConfig(name=name)
        else:
            config.name = name
            
        super().__init__(config)
        self.sink_func = sink_func
    
    async def process(self, data: Any) -> Any:
        """
        Write data to the configured destination.
        
        Args:
            data: Data to write
            
        Returns:
            The original data (for potential chaining)
        """
        try:
            result = self.sink_func(data)
            if asyncio.iscoroutine(result):
                await result
            return data  # Return original data for chaining
        except Exception as e:
            raise PipelineExecutionError(f"Sink write failed: {e}", self.id) from e


class BatchProcessingPipeline(BasePipeline):
    """Pipeline for processing data in batches."""
    
    def __init__(
        self,
        name: str,
        batch_func: Callable,
        config: Optional[PipelineConfig] = None
    ):
        """
        Initialize the batch processing pipeline.
        
        Args:
            name: Name of the pipeline
            batch_func: Function to process a batch of data
            config: Pipeline configuration
        """
        if config is None:
            config = PipelineConfig(name=name)
        else:
            config.name = name
            
        super().__init__(config)
        self.batch_func = batch_func
    
    async def process(self, data: Any) -> Any:
        """
        Process data in batches.
        
        Args:
            data: Input data (should be iterable for batching)
            
        Returns:
            Processed batch results
        """
        if not hasattr(data, '__iter__') or isinstance(data, (str, bytes)):
            # Single item, process as is
            try:
                result = self.batch_func([data])
                if asyncio.iscoroutine(result):
                    result = await result
                return result[0] if result else None
            except Exception as e:
                raise PipelineExecutionError(f"Batch processing failed: {e}", self.id) from e
        
        # Process in batches
        batch_size = self.config.batch_size
        results = []
        
        try:
            data_list = list(data)
            
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i:i + batch_size]
                
                result = self.batch_func(batch)
                if asyncio.iscoroutine(result):
                    result = await result
                
                if isinstance(result, (list, tuple)):
                    results.extend(result)
                else:
                    results.append(result)
            
            return results
            
        except Exception as e:
            raise PipelineExecutionError(f"Batch processing failed: {e}", self.id) from e


class AggregationPipeline(BasePipeline):
    """Pipeline for aggregating data using various functions."""
    
    def __init__(
        self,
        name: str,
        aggregation_func: Callable,
        config: Optional[PipelineConfig] = None
    ):
        """
        Initialize the aggregation pipeline.
        
        Args:
            name: Name of the pipeline
            aggregation_func: Function to aggregate data
            config: Pipeline configuration
        """
        if config is None:
            config = PipelineConfig(name=name)
        else:
            config.name = name
            
        super().__init__(config)
        self.aggregation_func = aggregation_func
    
    async def process(self, data: Any) -> Any:
        """
        Aggregate the input data.
        
        Args:
            data: Input data to aggregate
            
        Returns:
            Aggregated result
        """
        try:
            result = self.aggregation_func(data)
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as e:
            raise PipelineExecutionError(f"Aggregation failed: {e}", self.id) from e