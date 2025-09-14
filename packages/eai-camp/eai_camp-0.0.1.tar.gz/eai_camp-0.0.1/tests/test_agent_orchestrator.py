"""Tests for Agent Orchestrator"""

import pytest
import asyncio
from datetime import datetime

from eai_camp.core.agent_orchestrator import AgentOrchestrator, AgentStatus
from eai_camp.core.audit_manager import AuditManager
from eai_camp.agents.base_agent import BaseAgent, AgentConfig

class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    async def _execute(self):
        return {"success": True, "message": "Mock execution completed"}

@pytest.fixture
def orchestrator():
    """Create orchestrator for testing"""
    audit_manager = AuditManager()
    return AgentOrchestrator(audit_manager)

@pytest.fixture
def mock_agent():
    """Create mock agent for testing"""
    config = AgentConfig(
        name="Test Agent",
        description="Agent for testing",
        monitoring_interval=1
    )
    return MockAgent(config)

@pytest.mark.asyncio
async def test_register_agent(orchestrator, mock_agent):
    """Test agent registration"""
    agent_id = await orchestrator.register_agent(
        agent=mock_agent,
        name="Test Agent",
        owner="test_user",
        tags=["test"],
        configuration={"param1": "value1"}
    )
    
    assert agent_id is not None
    assert len(agent_id) > 0
    assert agent_id in orchestrator.agents
    assert agent_id in orchestrator.agent_metadata
    
    # Check metadata
    metadata = orchestrator.agent_metadata[agent_id]
    assert metadata.name == "Test Agent"
    assert metadata.owner == "test_user"
    assert "test" in metadata.tags
    assert metadata.status == AgentStatus.CREATED

@pytest.mark.asyncio
async def test_start_stop_agent(orchestrator, mock_agent):
    """Test starting and stopping an agent"""
    # Register agent
    agent_id = await orchestrator.register_agent(
        agent=mock_agent,
        name="Test Agent",
        owner="test_user"
    )
    
    # Start agent
    success = await orchestrator.start_agent(agent_id)
    assert success is True
    
    metadata = orchestrator.agent_metadata[agent_id]
    assert metadata.status == AgentStatus.RUNNING
    
    # Wait a moment for the agent to run
    await asyncio.sleep(0.1)
    
    # Stop agent
    success = await orchestrator.stop_agent(agent_id)
    assert success is True
    
    metadata = orchestrator.agent_metadata[agent_id]
    assert metadata.status == AgentStatus.STOPPED

@pytest.mark.asyncio
async def test_pause_resume_agent(orchestrator, mock_agent):
    """Test pausing and resuming an agent"""
    # Register and start agent
    agent_id = await orchestrator.register_agent(
        agent=mock_agent,
        name="Test Agent",
        owner="test_user"
    )
    
    await orchestrator.start_agent(agent_id)
    
    # Pause agent
    success = await orchestrator.pause_agent(agent_id)
    assert success is True
    
    metadata = orchestrator.agent_metadata[agent_id]
    assert metadata.status == AgentStatus.PAUSED
    
    # Resume agent
    success = await orchestrator.resume_agent(agent_id)
    assert success is True
    
    metadata = orchestrator.agent_metadata[agent_id]
    assert metadata.status == AgentStatus.RUNNING
    
    # Cleanup
    await orchestrator.stop_agent(agent_id)

def test_list_agents(orchestrator, mock_agent):
    """Test listing agents"""
    # Initially empty
    agents = orchestrator.list_agents()
    assert len(agents) == 0
    
    # Register agent
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    agent_id = loop.run_until_complete(
        orchestrator.register_agent(
            agent=mock_agent,
            name="Test Agent",
            owner="test_user"
        )
    )
    
    loop.close()
    
    # Check list
    agents = orchestrator.list_agents()
    assert len(agents) == 1
    assert agents[0]['agent_id'] == agent_id

def test_get_agent_status(orchestrator, mock_agent):
    """Test getting agent status"""
    # Register agent
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    agent_id = loop.run_until_complete(
        orchestrator.register_agent(
            agent=mock_agent,
            name="Test Agent",
            owner="test_user"
        )
    )
    
    loop.close()
    
    # Get status
    status = orchestrator.get_agent_status(agent_id)
    assert status is not None
    assert status['agent_id'] == agent_id
    assert status['name'] == "Test Agent"
    assert status['status'] == AgentStatus.CREATED.value

if __name__ == "__main__":
    pytest.main([__file__])
