"""Tests for Compliance Engine"""

import pytest
import asyncio
from datetime import datetime, timedelta

from eai_camp.core.compliance_engine import ComplianceEngine, ComplianceFramework, ViolationSeverity
from eai_camp.core.audit_manager import AuditManager

@pytest.fixture
def compliance_engine():
    """Create compliance engine for testing"""
    audit_manager = AuditManager()
    return ComplianceEngine(audit_manager)

@pytest.mark.asyncio
async def test_gdpr_data_minimization_compliant(compliance_engine):
    """Test GDPR data minimization - compliant scenario"""
    agent_data = {
        "processed_data": {"name": "John Doe", "email": "john@example.com"},
        "data_processing_justification": "Customer support"
    }
    
    is_compliant, details = await compliance_engine.check_data_minimization(
        agent_data, {"max_data_fields": 10, "required_justification": True}
    )
    
    assert is_compliant is True
    assert details["personal_data_fields_count"] <= 10
    assert details["has_justification"] is True

@pytest.mark.asyncio
async def test_gdpr_data_minimization_violation(compliance_engine):
    """Test GDPR data minimization - violation scenario"""
    agent_data = {
        "processed_data": {
            "name": "John Doe", "email": "john@example.com", "phone": "123-456-7890",
            "address": "123 Main St", "ssn": "123-45-6789", "birth_date": "1990-01-01",
            "personal_notes": "Notes", "medical_history": "History", 
            "financial_info": "Info", "preferences": "Prefs", "social_media": "SM",
            "extra_field": "Extra"
        }
    }
    
    is_compliant, details = await compliance_engine.check_data_minimization(
        agent_data, {"max_data_fields": 10, "required_justification": True}
    )
    
    assert is_compliant is False
    assert details["personal_data_fields_count"] > 10
    assert details["has_justification"] is False

@pytest.mark.asyncio
async def test_gdpr_consent_verification_compliant(compliance_engine):
    """Test GDPR consent verification - compliant scenario"""
    agent_data = {
        "user_consent": {
            "granted": True,
            "type": "explicit",
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    is_compliant, details = await compliance_engine.check_consent_verification(
        agent_data, {"require_explicit_consent": True}
    )
    
    assert is_compliant is True
    assert details["has_consent"] is True
    assert details["consent_type"] == "explicit"

@pytest.mark.asyncio
async def test_gdpr_consent_verification_violation(compliance_engine):
    """Test GDPR consent verification - violation scenario"""
    agent_data = {
        "user_consent": {
            "granted": False,
            "type": "none",
            "timestamp": None
        }
    }
    
    is_compliant, details = await compliance_engine.check_consent_verification(
        agent_data, {"require_explicit_consent": True}
    )
    
    assert is_compliant is False
    assert details["has_consent"] is False

@pytest.mark.asyncio
async def test_data_retention_compliant(compliance_engine):
    """Test data retention - compliant scenario"""
    recent_time = datetime.utcnow() - timedelta(days=30)
    agent_data = {
        "data_created_timestamp": recent_time.isoformat()
    }
    
    is_compliant, details = await compliance_engine.check_data_retention(
        agent_data, {"max_retention_days": 730}
    )
    
    assert is_compliant is True
    assert details["days_retained"] <= 730

@pytest.mark.asyncio
async def test_data_retention_violation(compliance_engine):
    """Test data retention - violation scenario"""
    old_time = datetime.utcnow() - timedelta(days=800)
    agent_data = {
        "data_created_timestamp": old_time.isoformat()
    }
    
    is_compliant, details = await compliance_engine.check_data_retention(
        agent_data, {"max_retention_days": 730}
    )
    
    assert is_compliant is False
    assert details["days_retained"] > 730
    assert details["should_delete"] is True

@pytest.mark.asyncio
async def test_full_compliance_check(compliance_engine):
    """Test full compliance check"""
    # Compliant agent data
    agent_data = {
        "processed_data": {"name": "John Doe", "email": "john@example.com"},
        "data_processing_justification": "Customer support",
        "user_consent": {
            "granted": True,
            "type": "explicit",
            "timestamp": datetime.utcnow().isoformat()
        },
        "data_created_timestamp": datetime.utcnow().isoformat(),
        "access_control": {
            "authenticated": True,
            "user_role": "medical_staff"
        },
        "data_transmission": {
            "encrypted": True,
            "encryption_type": "AES256"
        }
    }
    
    is_compliant, violations, risk_score = await compliance_engine.check_agent_compliance(
        agent_id="test_agent_001",
        agent_data=agent_data,
        frameworks=[ComplianceFramework.GDPR, ComplianceFramework.HIPAA]
    )
    
    assert isinstance(is_compliant, bool)
    assert isinstance(violations, list)
    assert isinstance(risk_score, float)
    assert 0 <= risk_score <= 100

def test_violation_summary(compliance_engine):
    """Test violation summary functionality"""
    summary = compliance_engine.get_violation_summary()
    
    assert "total_violations" in summary
    assert "unresolved_violations" in summary
    assert "by_severity" in summary
    assert "by_framework" in summary

if __name__ == "__main__":
    pytest.main([__file__])
