"""
Ultimate test file targeting 100% complete coverage
"""

import pytest
import os
import sys
import shutil
import yaml
import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open, call, ANY
from click.testing import CliRunner
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from specpulse.cli.main import SpecPulseCLI, main
from specpulse.core.specpulse import SpecPulse
from specpulse.core.validator import Validator
from specpulse.utils.console import Console
from specpulse.utils.git_utils import GitUtils


class TestValidator100Percent:
    """Cover the last 2 lines in validator.py"""
    
    def test_validator_lines_172_228(self, tmp_path):
        """Cover lines 172 and 228 - missing sections without fix"""
        project_path = tmp_path / "project"
        project_path.mkdir()
        
        # Create structure
        for dir_name in [".specpulse", "memory", "specs", "plans", "templates", "scripts"]:
            (project_path / dir_name).mkdir()
        
        config = {"constitution": {"enforce": True}}
        (project_path / ".specpulse" / "config.yaml").write_text(yaml.dump(config))
        (project_path / "memory" / "constitution.md").write_text("# Constitution")
        
        validator = Validator()
        
        # Test line 172 - spec missing sections, fix=False
        spec_dir = project_path / "specs" / "spec001"
        spec_dir.mkdir()
        spec_path = spec_dir / "spec.md"
        spec_path.write_text("# Test Spec\n## Some Section\nContent")  # Missing required sections
        
        results = validator.validate_spec(project_path, "spec001", fix=False, verbose=False)
        assert any("Missing sections" in r.get("message", "") for r in results)
        
        # Test line 228 - plan missing sections, fix=False
        plan_dir = project_path / "plans" / "plan001"
        plan_dir.mkdir()
        plan_path = plan_dir / "plan.md"
        plan_path.write_text("# Test Plan\n## Some Section\nContent")  # Missing required sections
        
        results = validator.validate_plan(project_path, "plan001", fix=False, verbose=False)
        assert any("Missing sections" in r.get("message", "") for r in results)


class TestCLIComplete:
    """Complete CLI coverage"""
    
    def test_cli_missing_lines(self, tmp_path, monkeypatch):
        """Cover lines 236-237, 242, 274, 336-381, 385-413, 617-658, 662-738"""
        monkeypatch.chdir(tmp_path)
        cli = SpecPulseCLI()
        
        # Initialize project for testing
        cli.init("test-project")
        os.chdir(tmp_path / "test-project")
        
        # Lines 236-237: validate with component="spec" but validator returns success
        with patch('specpulse.cli.main.Validator') as mock_validator:
            mock_instance = Mock()
            mock_validator.return_value = mock_instance
            mock_instance.validate_spec.return_value = [
                {"status": "success", "message": "Valid"}
            ]
            cli2 = SpecPulseCLI()
            result = cli2.validate(component="spec")
            assert result is True
            
            # Test with errors
            mock_instance.validate_spec.return_value = [
                {"status": "error", "message": "Invalid"}
            ]
            result = cli2.validate(component="spec")
            assert result is False
        
        # Line 242: unknown component
        result = cli.validate(component="unknown_component")
        assert result is False
        
        # Line 274: update with subprocess
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Updated", stderr="")
            result = cli.update()
            assert result is True
        
        # Lines 336-381: Private helper methods (called by init)
        # These are already covered when we call init()
        
        # Lines 385-413: decompose method entry and checks
        # Create specs for decompose testing
        specs_dir = tmp_path / "test-project" / "specs"
        spec_dir = specs_dir / "001-feature"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("""
# Feature Spec
## Requirements
- User authentication
- Data storage
## User Stories
- As a user, I want to login
## Acceptance Criteria
- Login works
        """)
        
        # Test decompose with specific spec_id
        result = cli.decompose("001-feature")
        assert result is True
        
        # Test decompose with partial match
        result = cli.decompose("001")
        assert result is True
        
        # Lines 617-658: decompose helper methods
        spec_data = {
            "title": "Test",
            "content": "Content",
            "requirements": ["Req1"],
            "services": [{"name": "service1", "description": "Service 1"}]
        }
        
        cli._generate_microservices(spec_dir, spec_data)
        cli._generate_api_contracts(spec_dir, spec_data)
        cli._generate_interfaces(spec_dir, spec_data)
        
        # Lines 662-738: More helper methods
        content = cli._parse_spec_content("# Spec\n## Requirements\nTest")
        assert content is not None
        
        boundaries = cli._analyze_domain_boundaries(spec_data)
        assert boundaries is not None
        
        services = cli._extract_services(spec_data)
        assert isinstance(services, list)
        
        contracts = cli._generate_service_contracts(services)
        assert contracts is not None
        
        interfaces = cli._create_interface_definitions(services)
        assert interfaces is not None
    
    def test_cli_main_entry_complete(self):
        """Cover lines 743-806 - main CLI entry"""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Test all CLI commands with various options
            result = runner.invoke(main, ['--help'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['--version'])
            assert result.exit_code == 0
            
            # Test init with various options
            result = runner.invoke(main, ['init', 'my-project'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['init', '--here'])
            assert result.exit_code == 0
            
            os.chdir('my-project')
            
            # Test validate with all options
            result = runner.invoke(main, ['validate'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['validate', '--component', 'specs'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['validate', '--component', 'plans'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['validate', '--component', 'constitution'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['validate', '--fix'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['validate', '--verbose'])
            assert result.exit_code == 0
            
            # Test sync
            result = runner.invoke(main, ['sync'])
            assert result.exit_code == 0
            
            # Test doctor
            result = runner.invoke(main, ['doctor'])
            assert result.exit_code == 0
            
            # Test update
            result = runner.invoke(main, ['update'])
            # May succeed or fail depending on environment
            
            # Create spec for decompose
            spec_dir = Path('specs') / '001-test'
            spec_dir.mkdir(parents=True)
            (spec_dir / 'spec.md').write_text("""
# Test Spec
## Requirements
- Requirement 1
## User Stories
- Story 1
## Acceptance Criteria
- Criteria 1
            """)
            
            # Test decompose with all combinations
            result = runner.invoke(main, ['decompose'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['decompose', '001'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['decompose', '001', '--all'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['decompose', '001', '--microservices', '--apis', '--interfaces'])
            assert result.exit_code == 0


class TestSpecPulseComplete:
    """Complete SpecPulse core coverage"""
    
    def test_specpulse_all_methods(self, tmp_path):
        """Cover all remaining lines in specpulse.py"""
        # Lines 25-32: init variations
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            sp = SpecPulse()
            assert sp.project_path == tmp_path
            
            sp2 = SpecPulse(tmp_path)
            assert sp2.project_path == tmp_path
        finally:
            os.chdir(original_cwd)
        
        project_path = tmp_path / "project"
        project_path.mkdir()
        
        # Test all template loading methods
        sp = SpecPulse(project_path)
        
        # Lines 38-39, 46-47, 130-131, 333: Check for template files
        templates_dir = project_path / "templates"
        templates_dir.mkdir()
        
        # Test when template files don't exist (use defaults)
        assert "SpecPulse" in sp.get_spec_template()
        assert "SpecPulse" in sp.get_plan_template()
        assert "SpecPulse" in sp.get_task_template()
        assert "SpecPulse" in sp.get_constitution_template()
        assert "Context" in sp.get_context_template()
        assert "Decision" in sp.get_decisions_template()
        
        # Create template files
        (templates_dir / "spec.md").write_text("Custom spec template")
        (templates_dir / "plan.md").write_text("Custom plan template")
        (templates_dir / "task.md").write_text("Custom task template")
        (templates_dir / "constitution.md").write_text("Custom constitution")
        (templates_dir / "context.md").write_text("Custom context")
        (templates_dir / "decisions.md").write_text("Custom decisions")
        
        # Reinitialize to load custom templates
        sp = SpecPulse(project_path)
        
        # Lines 423, 503, 577, 597-602, 651-656, 694-699, 741-746: Script templates
        scripts_dir = project_path / "scripts"
        scripts_dir.mkdir()
        
        # Test default scripts
        assert "#!/bin/bash" in sp.get_setup_script()
        assert "#!/bin/bash" in sp.get_spec_script()
        assert "#!/bin/bash" in sp.get_plan_script()
        assert "#!/bin/bash" in sp.get_task_script()
        assert "#!/bin/bash" in sp.get_validate_script()
        assert "#!/bin/bash" in sp.get_generate_script()
        assert "#!/bin/bash" in sp.get_decompose_script()
        
        # Create custom scripts
        (scripts_dir / "sp-pulse-init.sh").write_text("#!/bin/bash\ncustom init")
        (scripts_dir / "sp-pulse-spec.sh").write_text("#!/bin/bash\ncustom spec")
        (scripts_dir / "sp-pulse-plan.sh").write_text("#!/bin/bash\ncustom plan")
        (scripts_dir / "sp-pulse-task.sh").write_text("#!/bin/bash\ncustom task")
        (scripts_dir / "sp-pulse-validate.sh").write_text("#!/bin/bash\ncustom validate")
        (scripts_dir / "sp-pulse-generate.sh").write_text("#!/bin/bash\ncustom generate")
        (scripts_dir / "sp-pulse-decompose.sh").write_text("#!/bin/bash\ncustom decompose")
        
        # Reinitialize to load custom scripts
        sp = SpecPulse(project_path)
        
        # Lines 556-568: Decomposition templates
        decomp_dir = templates_dir / "decomposition"
        decomp_dir.mkdir()
        
        # Test default decomposition templates
        assert "Microservices" in sp.get_decomposition_template("microservices")
        assert "openapi" in sp.get_decomposition_template("api")
        assert "interface" in sp.get_decomposition_template("interface")
        assert "Integration" in sp.get_decomposition_template("integration")
        assert "Service" in sp.get_decomposition_template("service_plan")
        
        # Create custom decomposition templates
        (decomp_dir / "microservices.md").write_text("Custom microservices")
        (decomp_dir / "api-contract.yaml").write_text("Custom API")
        (decomp_dir / "interface.ts").write_text("Custom interface")
        (decomp_dir / "integration-plan.md").write_text("Custom integration")
        (decomp_dir / "service-plan.md").write_text("Custom service")
        
        # Reinitialize
        sp = SpecPulse(project_path)
        
        # Lines 791, 842, 870: AI instructions
        claude_dir = project_path / ".claude"
        claude_dir.mkdir()
        gemini_dir = project_path / ".gemini"
        gemini_dir.mkdir()
        
        # Test default instructions
        assert "Claude" in sp.get_claude_instructions()
        assert "Gemini" in sp.get_gemini_instructions()
        assert "decompose" in sp.get_claude_decompose_instructions()
        
        # Create custom instructions
        (claude_dir / "INSTRUCTIONS.md").write_text("Custom Claude instructions")
        (claude_dir / "DECOMPOSE_INSTRUCTIONS.md").write_text("Custom decompose instructions")
        (gemini_dir / "INSTRUCTIONS.md").write_text("Custom Gemini instructions")
        
        # Reinitialize
        sp = SpecPulse(project_path)
        
        # Lines 953-1018: Command templates
        claude_commands = claude_dir / "commands"
        claude_commands.mkdir()
        gemini_commands = gemini_dir / "commands"
        gemini_commands.mkdir()
        
        # Test default commands
        assert "pulse" in sp.get_claude_pulse_command()
        assert "spec" in sp.get_claude_spec_command()
        assert "plan" in sp.get_claude_plan_command()
        assert "task" in sp.get_claude_task_command()
        assert "decompose" in sp.get_claude_decompose_command()
        
        assert "pulse" in sp.get_gemini_pulse_command()
        assert "spec" in sp.get_gemini_spec_command()
        assert "plan" in sp.get_gemini_plan_command()
        assert "task" in sp.get_gemini_task_command()
        assert "decompose" in sp.get_gemini_decompose_command()
        
        # Create custom commands
        (claude_commands / "sp-pulse.md").write_text("Custom Claude pulse")
        (claude_commands / "sp-spec.md").write_text("Custom Claude spec")
        (claude_commands / "sp-plan.md").write_text("Custom Claude plan")
        (claude_commands / "sp-task.md").write_text("Custom Claude task")
        (claude_commands / "sp-decompose.md").write_text("Custom Claude decompose")
        
        (gemini_commands / "sp-pulse.toml").write_text("Custom Gemini pulse")
        (gemini_commands / "sp-spec.toml").write_text("Custom Gemini spec")
        (gemini_commands / "sp-plan.toml").write_text("Custom Gemini plan")
        (gemini_commands / "sp-task.toml").write_text("Custom Gemini task")
        (gemini_commands / "sp-decompose.toml").write_text("Custom Gemini decompose")
        
        # Reinitialize to load custom commands
        sp = SpecPulse(project_path)
        
        # Verify all methods work
        assert sp.get_spec_template() is not None
        assert sp.get_plan_template() is not None
        assert sp.get_task_template() is not None
        assert sp.get_constitution_template() is not None
        assert sp.get_context_template() is not None
        assert sp.get_decisions_template() is not None
        
        assert sp.get_setup_script() is not None
        assert sp.get_spec_script() is not None
        assert sp.get_plan_script() is not None
        assert sp.get_task_script() is not None
        assert sp.get_validate_script() is not None
        assert sp.get_generate_script() is not None
        assert sp.get_decompose_script() is not None
        
        assert sp.get_decomposition_template("microservices") is not None
        assert sp.get_decomposition_template("api") is not None
        assert sp.get_decomposition_template("interface") is not None
        assert sp.get_decomposition_template("integration") is not None
        assert sp.get_decomposition_template("service_plan") is not None
        
        assert sp.get_claude_instructions() is not None
        assert sp.get_gemini_instructions() is not None
        assert sp.get_claude_decompose_instructions() is not None
        
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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=specpulse", "--cov-report=term-missing"])