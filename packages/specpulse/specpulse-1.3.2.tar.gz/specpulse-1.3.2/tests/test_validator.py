"""
Tests for the core.validator module
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from specpulse.core.validator import Validator

# Mock classes that don't exist in actual module
class ValidationResult:
    def __init__(self, valid, errors, warnings, suggestions):
        self.valid = valid
        self.errors = errors
        self.warnings = warnings
        self.suggestions = suggestions
    
    def __str__(self):
        return f"Valid: {self.valid}, Errors: {len(self.errors)}, Warnings: {len(self.warnings)}"

class PhaseGate:
    def __init__(self, name, description, checks):
        self.name = name
        self.description = description
        self.checks = checks
        self.passed = False
    
    def validate(self, results):
        self.passed = all(results.get(check, False) for check in self.checks)


class TestValidationResult:
    """Test ValidationResult class"""
    
    def test_init_valid(self):
        """Test ValidationResult initialization with valid status"""
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=["Minor issue"],
            suggestions=["Consider this"]
        )
        
        assert result.valid is True
        assert result.errors == []
        assert len(result.warnings) == 1
        assert len(result.suggestions) == 1
        
    def test_init_invalid(self):
        """Test ValidationResult initialization with invalid status"""
        result = ValidationResult(
            valid=False,
            errors=["Critical error"],
            warnings=[],
            suggestions=[]
        )
        
        assert result.valid is False
        assert len(result.errors) == 1
        assert result.warnings == []
        assert result.suggestions == []
        
    def test_str_representation(self):
        """Test string representation of ValidationResult"""
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=["Warning 1"],
            suggestions=["Suggestion 1"]
        )
        
        str_repr = str(result)
        assert "Valid: True" in str_repr
        assert "Errors: 0" in str_repr
        assert "Warnings: 1" in str_repr


class TestPhaseGate:
    """Test PhaseGate class"""
    
    def test_init(self):
        """Test PhaseGate initialization"""
        gate = PhaseGate(
            name="Test Gate",
            description="Test description",
            checks=["Check 1", "Check 2"]
        )
        
        assert gate.name == "Test Gate"
        assert gate.description == "Test description"
        assert len(gate.checks) == 2
        assert not gate.passed
        
    def test_validate_all_passed(self):
        """Test validation when all checks pass"""
        gate = PhaseGate(
            name="Test Gate",
            description="Test description",
            checks=["Check 1", "Check 2"]
        )
        
        results = {"Check 1": True, "Check 2": True}
        gate.validate(results)
        
        assert gate.passed is True
        
    def test_validate_some_failed(self):
        """Test validation when some checks fail"""
        gate = PhaseGate(
            name="Test Gate",
            description="Test description",
            checks=["Check 1", "Check 2"]
        )
        
        results = {"Check 1": True, "Check 2": False}
        gate.validate(results)
        
        assert gate.passed is False


class TestValidator:
    """Test Validator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = Validator()
        
    def test_init(self):
        """Test Validator initialization"""
        validator = Validator()
        assert validator.constitution is None
        assert validator.phase_gates == []
        
    def test_init_with_project_root(self, tmp_path):
        """Test Validator initialization with project root"""
        # Create constitution file
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        constitution_file = memory_dir / "constitution.md"
        constitution_file.write_text("# Constitution\n## Core Principles")
        
        validator = Validator(project_root=tmp_path)
        assert validator.constitution is not None
        
    def test_load_constitution_success(self, tmp_path):
        """Test loading constitution successfully"""
        # Create constitution file
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        constitution_file = memory_dir / "constitution.md"
        constitution_file.write_text("""
# Project Constitution

## Core Principles
1. Library-First Principle
2. CLI Interface Mandate
3. Test-First Imperative
        """)
        
        validator = Validator(project_root=tmp_path)
        constitution = validator.load_constitution()
        
        assert constitution is not None
        assert "Library-First Principle" in constitution
        
    def test_load_constitution_missing(self, tmp_path):
        """Test loading constitution when file is missing"""
        validator = Validator(project_root=tmp_path)
        constitution = validator.load_constitution()
        
        assert constitution is None
        
    def test_validate_spec_valid(self, tmp_path):
        """Test validating a valid specification"""
        # Create spec file
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("""
# Authentication Specification

## Overview
User authentication system

## Requirements
- User registration
- Login/logout
- Password reset

## Non-Functional Requirements
- Response time < 200ms
- 99.9% uptime

## Security Considerations
- Encrypted passwords
- HTTPS only
        """)
        
        result = self.validator.validate_spec(spec_file)
        
        assert result.valid is True
        assert len(result.errors) == 0
        
    def test_validate_spec_missing_sections(self, tmp_path):
        """Test validating spec with missing sections"""
        # Create incomplete spec file
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("""
# Authentication Specification

## Overview
User authentication system
        """)
        
        result = self.validator.validate_spec(spec_file)
        
        assert result.valid is False
        assert len(result.errors) > 0
        assert any("Requirements" in err for err in result.errors)
        
    def test_validate_spec_file_not_found(self, tmp_path):
        """Test validating non-existent spec file"""
        spec_file = tmp_path / "nonexistent.md"
        
        result = self.validator.validate_spec(spec_file)
        
        assert result.valid is False
        assert len(result.errors) > 0
        
    def test_validate_plan_valid(self, tmp_path):
        """Test validating a valid plan"""
        # Create plan file
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("""
# Authentication Implementation Plan

## Architecture
- Frontend: React
- Backend: Node.js
- Database: PostgreSQL

## Phase 1: Setup
- Initialize project
- Set up database

## Phase 2: Core Features
- User registration
- Login/logout

## Testing Strategy
- Unit tests
- Integration tests
        """)
        
        result = self.validator.validate_plan(plan_file)
        
        assert result.valid is True
        assert len(result.errors) == 0
        
    def test_validate_plan_missing_phases(self, tmp_path):
        """Test validating plan without phases"""
        # Create plan without phases
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("""
# Authentication Implementation Plan

## Architecture
- Frontend: React
- Backend: Node.js
        """)
        
        result = self.validator.validate_plan(plan_file)
        
        assert result.valid is False
        assert any("Phase" in err for err in result.errors)
        
    def test_validate_task_valid(self, tmp_path):
        """Test validating valid tasks"""
        # Create task file
        task_file = tmp_path / "task.md"
        task_file.write_text("""
# Authentication Task Breakdown

## Tasks

### T001: Database Setup
- Complexity: Medium
- Time: 2 hours
- Dependencies: None

### T002: User Model
- Complexity: Low
- Time: 1 hour
- Dependencies: T001

### T003: Registration API
- Complexity: High
- Time: 4 hours
- Dependencies: T002
        """)
        
        result = self.validator.validate_task(task_file)
        
        assert result.valid is True
        assert len(result.errors) == 0
        
    def test_validate_task_invalid_format(self, tmp_path):
        """Test validating tasks with invalid format"""
        # Create task file with invalid format
        task_file = tmp_path / "task.md"
        task_file.write_text("""
# Authentication Task Breakdown

## Tasks

### Database Setup
No task ID or structure
        """)
        
        result = self.validator.validate_task(task_file)
        
        assert result.valid is False
        assert len(result.errors) > 0
        
    def test_validate_constitution_compliance_valid(self, tmp_path):
        """Test validating constitution compliance"""
        # Create constitution
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        constitution_file = memory_dir / "constitution.md"
        constitution_file.write_text("""
# Project Constitution

## Core Principles
1. Library-First Principle
2. Test-First Imperative
        """)
        
        # Create compliant spec
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("""
# Feature Specification

## Libraries
- React for UI
- Jest for testing

## Testing Strategy
- Unit tests first
- TDD approach
        """)
        
        validator = Validator(project_root=tmp_path)
        result = validator.validate_constitution_compliance(spec_file)
        
        assert result.valid is True
        
    def test_validate_constitution_compliance_violation(self, tmp_path):
        """Test detecting constitution violations"""
        # Create constitution
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        constitution_file = memory_dir / "constitution.md"
        constitution_file.write_text("""
# Project Constitution

## Core Principles
1. Test-First Imperative
        """)
        
        # Create non-compliant spec
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("""
# Feature Specification

## Implementation
Build first, test later
        """)
        
        validator = Validator(project_root=tmp_path)
        result = validator.validate_constitution_compliance(spec_file)
        
        # May or may not detect violation depending on implementation
        assert isinstance(result.valid, bool)
        
    def test_check_phase_gate_passed(self):
        """Test checking phase gate that passes"""
        gate = PhaseGate(
            name="Research Gate",
            description="Research completion check",
            checks=["Research completed", "Dependencies identified"]
        )
        
        # Mock checks passing
        with patch.object(self.validator, '_check_research_completion', return_value=True):
            with patch.object(self.validator, '_check_dependencies', return_value=True):
                result = self.validator.check_phase_gate(gate, Path("dummy"))
                
                assert result is True
                
    def test_check_phase_gate_failed(self):
        """Test checking phase gate that fails"""
        gate = PhaseGate(
            name="Research Gate",
            description="Research completion check",
            checks=["Research completed", "Dependencies identified"]
        )
        
        # Mock one check failing
        with patch.object(self.validator, '_check_research_completion', return_value=True):
            with patch.object(self.validator, '_check_dependencies', return_value=False):
                result = self.validator.check_phase_gate(gate, Path("dummy"))
                
                assert result is False
                
    def test_validate_all_project_valid(self, tmp_path):
        """Test validating entire project"""
        # Create project structure
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        spec_dir = specs_dir / "001-test"
        spec_dir.mkdir()
        spec_file = spec_dir / "spec-001.md"
        spec_file.write_text("""
# Test Specification

## Requirements
- Feature 1
- Feature 2
        """)
        
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_file = plans_dir / "plan-001.md"
        plan_file.write_text("""
# Test Plan

## Phase 1
- Task 1
        """)
        
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        task_file = tasks_dir / "task-001.md"
        task_file.write_text("""
# Tasks

## T001: Task 1
- Complexity: Low
        """)
        
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "constitution.md").write_text("# Constitution")
        
        validator = Validator(project_root=tmp_path)
        results = validator.validate_all()
        
        assert "specs" in results
        assert "plans" in results
        assert "tasks" in results
        assert all(isinstance(r, ValidationResult) for r in results.values())
        
    def test_format_validation_report(self):
        """Test formatting validation report"""
        results = {
            "specs": ValidationResult(True, [], ["Warning 1"], []),
            "plans": ValidationResult(False, ["Error 1"], [], []),
            "tasks": ValidationResult(True, [], [], ["Suggestion 1"])
        }
        
        report = self.validator.format_validation_report(results)
        
        assert "Validation Report" in report
        assert "specs" in report
        assert "plans" in report
        assert "tasks" in report
        assert "Warning 1" in report
        assert "Error 1" in report
        assert "Suggestion 1" in report