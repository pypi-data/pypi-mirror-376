"""
Final test targeting 80% total coverage
Focusing on high-impact lines that will maximize coverage
"""

import pytest
import os
import sys
import shutil
import yaml
import subprocess
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open, call, ANY
from click.testing import CliRunner
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from specpulse.cli.main import SpecPulseCLI, main
from specpulse.core.specpulse import SpecPulse


class TestCLI80Percent:
    """Target 80% coverage for CLI"""
    
    def test_decompose_working_flow(self, tmp_path, monkeypatch):
        """Test decompose with working implementation"""
        monkeypatch.chdir(tmp_path)
        cli = SpecPulseCLI()
        cli.init("test")
        os.chdir(tmp_path / "test")
        
        # Create spec
        spec_dir = tmp_path / "test" / "specs" / "001-test"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("""
# Test Spec
## Requirements
- Requirement 1
- Requirement 2
## User Stories
- Story 1
## Acceptance Criteria
- Criteria 1
        """)
        
        # Test decompose - it will use default templates
        result = cli.decompose("001-test", microservices=True, apis=True, interfaces=True)
        assert result is True
        
        # Verify files were created
        assert (spec_dir / "microservices.md").exists()
        assert (spec_dir / "api-contracts").exists()
        assert (spec_dir / "interfaces").exists()
    
    def test_cli_entry_points(self):
        """Test main CLI entry points"""
        from click.testing import CliRunner
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Test init
            result = runner.invoke(main, ['init', 'project'])
            assert result.exit_code == 0
            
            os.chdir('project')
            
            # Test validate
            result = runner.invoke(main, ['validate'])
            assert result.exit_code == 0
            
            # Test sync
            result = runner.invoke(main, ['sync'])
            assert result.exit_code == 0
            
            # Test doctor
            result = runner.invoke(main, ['doctor'])
            assert result.exit_code == 0
            
            # Create spec for decompose
            spec_dir = Path('specs') / '001-test'
            spec_dir.mkdir(parents=True)
            (spec_dir / 'spec.md').write_text("# Test")
            
            # Test decompose
            result = runner.invoke(main, ['decompose', '001'])
            assert result.exit_code == 0


class TestSpecPulse80Percent:
    """Target 80% coverage for SpecPulse core"""
    
    def test_template_generation_methods(self, tmp_path):
        """Test template generation methods"""
        sp = SpecPulse(tmp_path)
        
        # Test generate methods that create content from templates
        content = sp.generate_spec_template("TestSpec", "Test description")
        assert "TestSpec" in content
        assert "Test description" in content
        
        content = sp.generate_plan_template("TestPlan", "spec-001")
        assert "TestPlan" in content
        assert "spec-001" in content
        
        content = sp.generate_task_template("T001", "Test task")
        assert "T001" in content
        assert "Test task" in content
        
        # Test decomposition generation methods
        spec_data = {
            "title": "Test Spec",
            "requirements": ["Req1", "Req2"],
            "services": [
                {"name": "service1", "description": "Service 1"},
                {"name": "service2", "description": "Service 2"}
            ]
        }
        
        content = sp.generate_microservices_template("spec-001", spec_data)
        assert "Microservices" in content
        assert "spec-001" in content
        
        content = sp.generate_api_contract_template("service1", {
            "endpoints": ["/api/v1/resource"],
            "methods": ["GET", "POST"]
        })
        assert "openapi" in content
        assert "service1" in content
        
        content = sp.generate_interface_template("Service1", {
            "properties": ["id", "name", "description"]
        })
        assert "interface" in content
        assert "Service1" in content
        
        content = sp.generate_integration_plan_template("spec-001", spec_data)
        assert "Integration" in content
        assert "spec-001" in content
    
    def test_public_methods(self, tmp_path):
        """Test public methods of SpecPulse"""
        sp = SpecPulse(tmp_path)
        
        # Test init_project
        project_path = tmp_path / "new-project"
        result = sp.init_project("new-project", tmp_path)
        assert result is True
        assert project_path.exists()
        
        # Test doctor
        result = sp.doctor()
        assert isinstance(result, dict)
        assert "status" in result
        
        # Test sync_templates
        result = sp.sync_templates()
        assert result is True
        
        # Test validate methods
        results = sp.validate_all()
        assert isinstance(results, list)
        
        results = sp.validate_spec()
        assert isinstance(results, list)
        
        results = sp.validate_plan()
        assert isinstance(results, list)
        
        results = sp.validate_constitution()
        assert isinstance(results, list)
        
        # Test list_specs
        specs = sp.list_specs()
        assert isinstance(specs, list)
        
        # Test decompose_spec
        specs_dir = tmp_path / "specs" / "001-test"
        specs_dir.mkdir(parents=True)
        (specs_dir / "spec.md").write_text("""
# Test Spec
## Requirements
- Req 1
## User Stories
- Story 1
## Acceptance Criteria
- Criteria 1
        """)
        
        result = sp.decompose_spec("001-test")
        assert result is True
    
    def test_all_getters(self, tmp_path):
        """Test all getter methods"""
        sp = SpecPulse(tmp_path)
        
        # Template getters
        assert sp.get_spec_template() is not None
        assert sp.get_plan_template() is not None
        assert sp.get_task_template() is not None
        assert sp.get_constitution_template() is not None
        assert sp.get_context_template() is not None
        assert sp.get_decisions_template() is not None
        
        # Script getters
        assert sp.get_setup_script() is not None
        assert sp.get_spec_script() is not None
        assert sp.get_plan_script() is not None
        assert sp.get_task_script() is not None
        assert sp.get_validate_script() is not None
        assert sp.get_generate_script() is not None
        assert sp.get_decompose_script() is not None
        
        # Decomposition template getters
        assert sp.get_decomposition_template("microservices") is not None
        assert sp.get_decomposition_template("api") is not None
        assert sp.get_decomposition_template("interface") is not None
        assert sp.get_decomposition_template("integration") is not None
        assert sp.get_decomposition_template("service_plan") is not None
        
        # AI instruction getters
        assert sp.get_claude_instructions() is not None
        assert sp.get_gemini_instructions() is not None
        assert sp.get_claude_decompose_instructions() is not None
        
        # Command getters
        assert sp.get_claude_pulse_command() is not None
        assert sp.get_claude_spec_command() is not None
        assert sp.get_claude_plan_command() is not None
        assert sp.get_claude_task_command() is not None
        assert sp.get_claude_decompose_command() is not None
        
        assert sp.get_gemini_pulse_command() is not None
        assert sp.get_gemini_spec_command() is not None
        assert sp.get_gemini_plan_command() is not None
        assert sp.get_gemini_task_command() is not None
        assert sp.get_gemini_decompose_command() is not None


class TestIntegration80Percent:
    """Integration tests for 80% coverage"""
    
    def test_full_workflow(self, tmp_path, monkeypatch):
        """Test complete workflow from init to decompose"""
        monkeypatch.chdir(tmp_path)
        
        # Initialize project
        cli = SpecPulseCLI()
        assert cli.init("my-project") is True
        
        project_path = tmp_path / "my-project"
        os.chdir(project_path)
        
        # Validate project
        assert cli.validate() is True
        assert cli.validate(component="all") is True
        assert cli.validate(component="constitution") is True
        
        # Sync templates
        assert cli.sync() is True
        
        # Run doctor
        assert cli.doctor() is True
        
        # Create a spec
        spec_dir = project_path / "specs" / "001-feature"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("""
# Feature Specification
## Overview
This is a test feature for the system.

## Requirements
- The system shall provide user authentication
- The system shall store user data securely
- The system shall provide API endpoints

## User Stories
- As a user, I want to login to the system
- As a user, I want to view my profile
- As an admin, I want to manage users

## Acceptance Criteria
- Users can login with email and password
- User data is encrypted at rest
- API uses JWT authentication
        """)
        
        # Validate specs
        assert cli.validate(component="specs") is True
        
        # Decompose the spec
        assert cli.decompose("001-feature") is True
        assert cli.decompose("001-feature", microservices=True) is True
        assert cli.decompose("001-feature", apis=True) is True
        assert cli.decompose("001-feature", interfaces=True) is True
        
        # Verify outputs exist
        assert (spec_dir / "microservices.md").exists()
        assert (spec_dir / "api-contracts").exists()
        assert (spec_dir / "interfaces").exists()
        
        # Test update (may fail but should run)
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            cli.update()
    
    def test_edge_cases(self, tmp_path, monkeypatch):
        """Test edge cases and error conditions"""
        monkeypatch.chdir(tmp_path)
        cli = SpecPulseCLI()
        
        # Test validate outside project
        result = cli.validate()
        assert result is False
        
        # Test decompose outside project
        result = cli.decompose()
        assert result is False
        
        # Test sync outside project
        result = cli.sync()
        assert result is False
        
        # Test doctor outside project
        result = cli.doctor()
        assert result is False
        
        # Initialize and test edge cases
        cli.init("test")
        os.chdir(tmp_path / "test")
        
        # Test decompose with non-existent spec
        result = cli.decompose("non-existent")
        assert result is False
        
        # Test validate with invalid component
        result = cli.validate(component="invalid_xyz_123")
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=specpulse", "--cov-report=term-missing"])