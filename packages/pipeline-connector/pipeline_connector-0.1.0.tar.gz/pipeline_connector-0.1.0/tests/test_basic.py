"""
Basic tests for the pipeline connector package.
"""

import asyncio
import sys
import os

# Add parent directory to path so we can import our package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipeline_connector import (
    PipelineManager,
    DataPipeline,
    BasePipeline,
    PipelineConfig,
    PipelineError,
    ConnectionType
)


async def test_pipeline_creation():
    """Test creating a basic pipeline."""
    print("Testing pipeline creation...")
    
    config = PipelineConfig(name="test_pipeline")
    
    class TestPipeline(BasePipeline):
        async def process(self, data):
            return data * 2
    
    pipeline = TestPipeline(config)
    
    assert pipeline.config.name == "test_pipeline"
    assert pipeline.id is not None
    
    result = await pipeline.execute(5)
    assert result == 10
    print("✓ Pipeline creation test passed")


async def test_data_pipeline():
    """Test data pipeline with transform function."""
    print("Testing data pipeline...")
    
    def double_values(data):
        return data * 2
    
    pipeline = DataPipeline("test", transform_func=double_values)
    
    result = await pipeline.execute(5)
    assert result == 10
    
    result = await pipeline.execute([1, 2, 3])
    assert result == [2, 4, 6]
    print("✓ Data pipeline test passed")


async def test_pipeline_manager():
    """Test pipeline manager functionality."""
    print("Testing pipeline manager...")
    
    manager = PipelineManager("test_manager")
    
    assert manager.name == "test_manager"
    assert len(manager.get_pipelines()) == 0
    assert len(manager.get_connections()) == 0
    
    pipeline1 = DataPipeline("p1", transform_func=lambda x: x * 2)
    pipeline2 = DataPipeline("p2", transform_func=lambda x: x + 10)
    
    manager.add_pipeline(pipeline1)
    manager.add_pipeline(pipeline2)
    
    connection_id = manager.connect(pipeline1, pipeline2)
    
    assert connection_id is not None
    assert len(manager.get_connections()) == 1
    print("✓ Pipeline manager test passed")


async def test_pipeline_execution():
    """Test executing connected pipelines."""
    print("Testing pipeline execution...")
    
    manager = PipelineManager()
    
    # Create simple transformation pipelines
    pipeline1 = DataPipeline("multiply", transform_func=lambda x: x * 2)
    pipeline2 = DataPipeline("add", transform_func=lambda x: x + 10)
    
    manager.add_pipeline(pipeline1)
    manager.add_pipeline(pipeline2)
    manager.connect(pipeline1, pipeline2)
    
    # Execute pipeline chain
    result = await manager.execute(5, start_pipeline=pipeline1)
    
    # 5 * 2 = 10, then 10 + 10 = 20
    assert result == 20
    print("✓ Pipeline execution test passed")


async def test_error_handling():
    """Test error handling."""
    print("Testing error handling...")
    
    class TestPipeline(BasePipeline):
        async def process(self, data):
            return data
    
    pipeline = TestPipeline()
    
    # Test with None input (should raise error)
    try:
        await pipeline.execute(None)
        assert False, "Should have raised an error"
    except PipelineError:
        pass  # Expected
    
    print("✓ Error handling test passed")


async def run_all_tests():
    """Run all tests."""
    print("=== Running Pipeline Connector Tests ===\n")
    
    try:
        await test_pipeline_creation()
        await test_data_pipeline()
        await test_pipeline_manager()
        await test_pipeline_execution()
        await test_error_handling()
        
        print("\n=== All tests passed! ===")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)