# EAI-CAMP: Enterprise AI Agent Compliance & Audit Management Platform

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**EAI-CAMP** is a comprehensive enterprise platform that addresses the critical gap between AI agent deployment and regulatory compliance. Unlike existing solutions that focus on either AI orchestration or compliance monitoring separately, EAI-CAMP provides a unified ecosystem for enterprises to develop, deploy, test, audit, and continuously monitor AI agents while ensuring full compliance with global regulatory frameworks.

## 🚀 Key Features

### Phase 1 Features (Current)
- **Agent Orchestration**: Register, start, stop, pause, and resume AI agents
- **Compliance Engine**: Real-time compliance checking against GDPR, HIPAA, SOX, and other frameworks
- **Audit Management**: Blockchain-style immutable audit trails with integrity verification
- **Interactive UI**: Streamlit-based dashboard for monitoring and management
- **Enterprise-Ready**: Multi-tenant architecture with role-based access control

### Supported Compliance Frameworks
- **GDPR** (General Data Protection Regulation)
- **HIPAA** (Health Insurance Portability and Accountability Act)
- **SOX** (Sarbanes-Oxley Act)
- **PCI-DSS** (Payment Card Industry Data Security Standard)
- **CCPA** (California Consumer Privacy Act)
- **ISO 27001** (Information Security Management)

## 📦 Installation

### From PyPI (After publishing)
```bash
pip install eai-camp
```

### From Source (Development)
```bash
git clone https://github.com/yourusername/eai-camp.git
cd eai-camp
pip install -e .
```

### For Development
```bash
git clone https://github.com/yourusername/eai-camp.git
cd eai-camp
pip install -e ".[dev]"
```

## 🏃 Quick Start

### 1. Launch the UI
```bash
streamlit run eai_camp/ui/app.py
```

### 2. Programmatic Usage
```python
import asyncio
from eai_camp.core.agent_orchestrator import AgentOrchestrator
from eai_camp.core.compliance_engine import ComplianceEngine
from eai_camp.agents.compliance_agent import ComplianceAgent
from eai_camp.agents.base_agent import AgentConfig

async def main():
    # Initialize core components
    orchestrator = AgentOrchestrator()
    compliance_engine = ComplianceEngine()
    
    # Create and register a compliance agent
    config = AgentConfig(
        name="My Compliance Agent",
        description="Monitors compliance across systems"
    )
    
    agent = ComplianceAgent(config, compliance_engine)
    
    agent_id = await orchestrator.register_agent(
        agent=agent,
        name=config.name,
        owner="admin",
        tags=["compliance", "monitoring"]
    )
    
    # Start the agent
    await orchestrator.start_agent(agent_id)
    print(f"Agent {agent_id} is now running!")
    
    # Stop after demo
    await asyncio.sleep(5)
    await orchestrator.stop_agent(agent_id)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=eai_camp --cov-report=html
```

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

We welcome contributions! Please feel free to submit a Pull Request.

---

**EAI-CAMP** - Bridging the gap between AI innovation and regulatory compliance.
