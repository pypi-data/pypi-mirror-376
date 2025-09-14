"""
EAI-CAMP: Enterprise AI Agent Compliance & Audit Management Platform
"""

__version__ = "0.1.0"
__author__ = "EAI-CAMP Development Team"
__email__ = "support@eai-camp.com"
__description__ = "Enterprise AI Agent Compliance & Audit Management Platform"

from .core.agent_orchestrator import AgentOrchestrator
from .core.compliance_engine import ComplianceEngine
from .core.audit_manager import AuditManager
from .agents.base_agent import BaseAgent
from .agents.compliance_agent import ComplianceAgent

__all__ = [
    "AgentOrchestrator",
    "ComplianceEngine", 
    "AuditManager",
    "BaseAgent",
    "ComplianceAgent"
]
