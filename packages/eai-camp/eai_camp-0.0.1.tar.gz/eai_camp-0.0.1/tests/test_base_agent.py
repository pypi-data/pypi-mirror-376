"""Tests for Base Agent"""

import pytest
import asyncio
from datetime import datetime

from eai_camp.agents.base_agent import BaseAgent, AgentConfig, AgentState

class TestAgent(BaseAgent):
    """Test implementation of BaseAgent"""
    
    def __init__(self, config, should_fail=False):
        super().__init__(config)
        self.should_fail = should_fail
        self.execution_count = 0
    
    async def _execute(self):
        self.execution_count += 1
        
        if self.should_fail:
            raise Exception("Simulated execution failure")
        
        await asyncio.sleep(0.01)  # Simulate work
        
        return {
            "success": True,
            "execution_count": self.execution_count,
            "timestamp": datetime.utcnow().isoformat()
        }

@pytest.fixture
def agent_config():
    """Create agent configuration for testing"""
    return AgentConfig(
        name="Test Agent",
        description="Agent for testing purposes",
        max_execution_time=60,
        retry_attempts=3,
        monitoring_interval=0.1,  # Fast interval for testing
        custom_params={"test_param": "test_value"}
    )

@pytest.fixture
def test_agent(agent_config):
    """Create test agent"""
    return TestAgent(agent_config)

@pytest.mark.asyncio
async def test_agent_start_stop(test_agent):
    """Test agent start and stop functionality"""
    # Initially idle
    assert test_agent.state == AgentState.IDLE
    
    # Start agent
    success = await test_agent.start()
    assert success is True
    assert test_agent.state == AgentState.RUNNING
    assert test_agent.start_time is not None
    
    # Let it run for a bit
    await asyncio.sleep(0.2)
    
    # Check that executions occurred
    assert test_agent.execution_count > 0
    assert test_agent.metrics["executions_count"] > 0
    
    # Stop agent
    success = await test_agent.stop()
    assert success is True
    assert test_agent.state == AgentState.STOPPED

@pytest.mark.asyncio
async def test_agent_pause_resume(test_agent):
    """Test agent pause and resume functionality"""
    # Start agent
    await test_agent.start()
    
    # Let it run
    await asyncio.sleep(0.1)
    execution_count_before_pause = test_agent.execution_count
    
    # Pause agent
    success = await test_agent.pause()
    assert success is True
    assert test_agent.state == AgentState.PAUSED
    
    # Wait and ensure no more executions
    await asyncio.sleep(0.1)
    assert test_agent.execution_count == execution_count_before_pause
    
    # Resume agent
    success = await test_agent.resume()
    assert success is True
    assert test_agent.state == AgentState.RUNNING
    
    # Let it run and check executions resumed
    await asyncio.sleep(0.1)
    assert test_agent.execution_count > execution_count_before_pause
    
    # Cleanup
    await test_agent.stop()

@pytest.mark.asyncio
async def test_agent_error_handling(agent_config):
    """Test agent error handling"""
    failing_agent = TestAgent(agent_config, should_fail=True)
    
    # Start agent
    await failing_agent.start()
    
    # Wait for execution to fail
    await asyncio.sleep(0.2)
    
    # Check that agent detected the error
    assert failing_agent.state == AgentState.ERROR
    assert failing_agent.metrics["failed_executions"] > 0

def test_agent_status(test_agent):
    """Test agent status reporting"""
    status = test_agent.get_status()
    
    assert status["agent_id"] is None  # Not set until registered
    assert status["name"] == "Test Agent"
    assert status["state"] == AgentState.IDLE.value
    assert "metrics" in status
    assert "recent_executions" in status

def test_agent_configuration(test_agent):
    """Test agent configuration retrieval"""
    config = test_agent.get_configuration()
    
    assert config["name"] == "Test Agent"
    assert config["description"] == "Agent for testing purposes"
    assert config["custom_params"]["test_param"] == "test_value"

@pytest.mark.asyncio
async def test_agent_metrics(test_agent):
    """Test agent metrics collection"""
    # Start and run agent
    await test_agent.start()
    await asyncio.sleep(0.2)
    await test_agent.stop()
    
    metrics = test_agent.metrics
    
    assert metrics["executions_count"] > 0
    assert metrics["successful_executions"] > 0
    assert metrics["failed_executions"] == 0
    assert metrics["total_execution_time"] > 0
    assert metrics["last_execution_time"] is not None

if __name__ == "__main__":
    pytest.main([__file__])
