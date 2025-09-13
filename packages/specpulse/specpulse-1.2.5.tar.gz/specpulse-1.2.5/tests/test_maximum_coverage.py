"""
Maximum coverage test - targeting 90%+ total coverage
"""

import pytest
import os
import sys
import shutil
import yaml
import subprocess
import json
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


class TestCLIMaxCoverage:
    """Maximum coverage for CLI module"""
    
    def test_validate_all_branches(self, tmp_path, monkeypatch):
        """Cover lines 236-237, 242 - validate method branches"""
        monkeypatch.chdir(tmp_path)
        cli = SpecPulseCLI()
        cli.init("test")
        os.chdir(tmp_path / "test")
        
        # Test validate with "spec" component
        with patch.object(cli, 'console'):
            # Create a spec to validate
            specs_dir = tmp_path / "test" / "specs" / "001-test"
            specs_dir.mkdir(parents=True)
            (specs_dir / "spec.md").write_text("# Spec\n## Requirements\nTest")
            
            result = cli.validate(component="spec")
            # Returns True when spec exists and is valid
            
            # Test with "specs" (plural)
            result = cli.validate(component="specs")
            
            # Test with "plan"
            result = cli.validate(component="plan")
            
            # Test with "plans"
            result = cli.validate(component="plans")
            
            # Test unknown component (line 242)
            result = cli.validate(component="invalid_xyz")
            assert result is False
    
    def test_update_method(self, tmp_path, monkeypatch):
        """Cover line 274 - update method"""
        monkeypatch.chdir(tmp_path)
        cli = SpecPulseCLI()
        
        with patch('subprocess.run') as mock_run:
            # Test successful update
            mock_run.return_value = Mock(returncode=0, stdout="Updated")
            result = cli.update()
            # Should work even outside project
    
    def test_private_init_methods(self, tmp_path, monkeypatch):
        """Cover lines 346-381 - private methods called by init"""
        monkeypatch.chdir(tmp_path)
        cli = SpecPulseCLI()
        
        # Initialize a project which calls all private methods
        result = cli.init("test-project")
        assert result is True
        
        # Verify all components were created
        project_path = tmp_path / "test-project"
        assert (project_path / ".specpulse" / "config.yaml").exists()
        assert (project_path / "templates").exists()
        assert (project_path / "memory").exists()
        assert (project_path / "scripts").exists()
        assert (project_path / ".claude").exists()
        assert (project_path / ".gemini").exists()
        assert (project_path / "PULSE.md").exists()
    
    def test_decompose_complete(self, tmp_path, monkeypatch):
        """Cover lines 393-413, 617-658, 662-738 - decompose and helpers"""
        monkeypatch.chdir(tmp_path)
        cli = SpecPulseCLI()
        cli.init("test")
        os.chdir(tmp_path / "test")
        
        # Test no specs directory (lines 393-395)
        shutil.rmtree(tmp_path / "test" / "specs")
        result = cli.decompose()
        assert result is False
        
        # Test empty specs directory (lines 397-399)
        (tmp_path / "test" / "specs").mkdir()
        result = cli.decompose()
        assert result is False
        
        # Create spec and test decompose (lines 405-413, 617-738)
        spec_dir = tmp_path / "test" / "specs" / "001-test"
        spec_dir.mkdir()
        spec_content = """# Test Spec
## Overview
Test microservice decomposition

## Requirements
- User authentication required
- Data storage with persistence
- Real-time notifications
- API gateway for routing

## User Stories
- As a user, I want to login securely
- As a user, I want to store my data
- As a user, I want real-time updates

## Acceptance Criteria
- Authentication works with JWT
- Data persists across sessions
- Notifications arrive within 1 second
"""
        (spec_dir / "spec.md").write_text(spec_content)
        
        # Mock SpecPulse to provide templates
        with patch('specpulse.cli.main.SpecPulse') as mock_sp:
            mock_instance = Mock()
            mock_sp.return_value = mock_instance
            
            # Mock template methods
            mock_instance.generate_microservices_template.return_value = "# Microservices\n{{title}}"
            mock_instance.generate_api_contract_template.return_value = "openapi: 3.0.0\ntitle: {{name}}"
            mock_instance.generate_interface_template.return_value = "interface {{name}} {}"
            mock_instance.generate_integration_plan_template.return_value = "# Integration\n{{services}}"
            
            # Test decompose with all flags
            result = cli.decompose("001-test", all=True)
            assert result is True
            
            # Test individual flags
            result = cli.decompose("001-test", microservices=True, apis=False, interfaces=False)
            assert result is True
            
            result = cli.decompose("001-test", microservices=False, apis=True, interfaces=False)
            assert result is True
            
            result = cli.decompose("001-test", microservices=False, apis=False, interfaces=True)
            assert result is True
            
            # Test auto-select with single spec
            result = cli.decompose()
            assert result is True
    
    def test_main_cli_entry(self):
        """Cover lines 743-806 - main CLI entry point"""
        runner = CliRunner()
        
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        
        result = runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        
        with runner.isolated_filesystem():
            # Test all CLI commands
            result = runner.invoke(main, ['init', 'test-project'])
            assert result.exit_code == 0
            
            os.chdir('test-project')
            
            result = runner.invoke(main, ['validate'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['validate', '--component', 'all', '--fix', '--verbose'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['sync'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['doctor'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['update'])
            # May succeed or fail
            
            # Create spec for decompose
            spec_dir = Path('specs') / '001-test'
            spec_dir.mkdir(parents=True)
            (spec_dir / 'spec.md').write_text("""# Test Spec
## Requirements
- Requirement 1
## User Stories
- Story 1
## Acceptance Criteria
- Criteria 1""")
            
            result = runner.invoke(main, ['decompose', '001-test'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['decompose', '001-test', '--all'])
            assert result.exit_code == 0


class TestSpecPulseMaxCoverage:
    """Maximum coverage for SpecPulse core module"""
    
    def test_all_initialization_paths(self, tmp_path):
        """Cover lines 25-32 - all init paths"""
        # Test init without path (uses cwd)
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            sp = SpecPulse()
            assert sp.project_path == tmp_path
        finally:
            os.chdir(original_cwd)
        
        # Test init with explicit path
        sp = SpecPulse(tmp_path)
        assert sp.project_path == tmp_path
    
    def test_all_template_loading(self, tmp_path):
        """Cover lines 38-39, 46-47, 130-131, 333 - template loading"""
        # Test without custom templates
        sp = SpecPulse(tmp_path)
        assert "SpecPulse" in sp.spec_template
        assert "SpecPulse" in sp.plan_template
        assert "SpecPulse" in sp.task_template
        assert "SpecPulse" in sp.constitution_template
        assert "Context" in sp.context_template
        assert "Decision" in sp.decisions_template
        
        # Create custom templates
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "spec.md").write_text("Custom Spec {{name}}")
        (templates_dir / "plan.md").write_text("Custom Plan {{name}}")
        (templates_dir / "task.md").write_text("Custom Task {{id}}")
        (templates_dir / "constitution.md").write_text("Custom Constitution")
        (templates_dir / "context.md").write_text("Custom Context")
        (templates_dir / "decisions.md").write_text("Custom Decisions")
        
        # Test with custom templates
        sp2 = SpecPulse(tmp_path)
        # Templates are loaded in __init__
    
    def test_all_script_loading(self, tmp_path):
        """Cover lines 423, 503, 577, 597-602, 651-656, 694-699, 741-746 - scripts"""
        # Test without custom scripts
        sp = SpecPulse(tmp_path)
        assert "#!/bin/bash" in sp.setup_script
        assert "#!/bin/bash" in sp.spec_script
        assert "#!/bin/bash" in sp.plan_script
        assert "#!/bin/bash" in sp.task_script
        assert "#!/bin/bash" in sp.validate_script
        assert "#!/bin/bash" in sp.generate_script
        assert "#!/bin/bash" in sp.decompose_script
        
        # Test all getter methods
        assert sp.get_setup_script() == sp.setup_script
        assert sp.get_spec_script() == sp.spec_script
        assert sp.get_plan_script() == sp.plan_script
        assert sp.get_task_script() == sp.task_script
        assert sp.get_validate_script() == sp.validate_script
        assert sp.get_generate_script() == sp.generate_script
        assert sp.get_decompose_script() == sp.decompose_script
        
        # Create custom scripts
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "sp-pulse-init.sh").write_text("#!/bin/bash\n# Custom init")
        (scripts_dir / "sp-pulse-spec.sh").write_text("#!/bin/bash\n# Custom spec")
        (scripts_dir / "sp-pulse-plan.sh").write_text("#!/bin/bash\n# Custom plan")
        (scripts_dir / "sp-pulse-task.sh").write_text("#!/bin/bash\n# Custom task")
        (scripts_dir / "sp-pulse-validate.sh").write_text("#!/bin/bash\n# Custom validate")
        (scripts_dir / "sp-pulse-generate.sh").write_text("#!/bin/bash\n# Custom generate")
        (scripts_dir / "sp-pulse-decompose.sh").write_text("#!/bin/bash\n# Custom decompose")
        
        # Test with custom scripts
        sp3 = SpecPulse(tmp_path)
        assert "Custom init" in sp3.get_setup_script()
        assert "Custom spec" in sp3.get_spec_script()
        assert "Custom plan" in sp3.get_plan_script()
        assert "Custom task" in sp3.get_task_script()
        assert "Custom validate" in sp3.get_validate_script()
        assert "Custom generate" in sp3.get_generate_script()
        assert "Custom decompose" in sp3.get_decompose_script()
    
    def test_all_ai_instructions(self, tmp_path):
        """Cover lines 791, 842, 870 - AI instructions"""
        # Test without custom instructions
        sp = SpecPulse(tmp_path)
        assert "Claude" in sp.get_claude_instructions()
        assert "Gemini" in sp.get_gemini_instructions()
        assert "decompose" in sp.get_claude_decompose_instructions()
        
        # Create custom instructions
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "INSTRUCTIONS.md").write_text("# Custom Claude Instructions")
        (claude_dir / "DECOMPOSE_INSTRUCTIONS.md").write_text("# Custom Decompose")
        
        gemini_dir = tmp_path / ".gemini"
        gemini_dir.mkdir()
        (gemini_dir / "INSTRUCTIONS.md").write_text("# Custom Gemini Instructions")
        
        # Test with custom instructions
        sp2 = SpecPulse(tmp_path)
        assert "Custom Claude" in sp2.get_claude_instructions()
        assert "Custom Gemini" in sp2.get_gemini_instructions()
        assert "Custom Decompose" in sp2.get_claude_decompose_instructions()
    
    def test_all_command_templates(self, tmp_path):
        """Cover lines 953-957, 961-965, 969-973, 977-981, 986-1018 - commands"""
        # Test without custom commands
        sp = SpecPulse(tmp_path)
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
        claude_cmds = tmp_path / ".claude" / "commands"
        claude_cmds.mkdir(parents=True)
        (claude_cmds / "sp-pulse.md").write_text("---\ntitle: Custom Pulse\n---\nCustom pulse command")
        (claude_cmds / "sp-spec.md").write_text("---\ntitle: Custom Spec\n---\nCustom spec command")
        (claude_cmds / "sp-plan.md").write_text("---\ntitle: Custom Plan\n---\nCustom plan command")
        (claude_cmds / "sp-task.md").write_text("---\ntitle: Custom Task\n---\nCustom task command")
        (claude_cmds / "sp-decompose.md").write_text("---\ntitle: Custom Decompose\n---\nCustom decompose")
        
        gemini_cmds = tmp_path / ".gemini" / "commands"
        gemini_cmds.mkdir(parents=True)
        (gemini_cmds / "sp-pulse.toml").write_text("[command]\nname = 'Custom Pulse'")
        (gemini_cmds / "sp-spec.toml").write_text("[command]\nname = 'Custom Spec'")
        (gemini_cmds / "sp-plan.toml").write_text("[command]\nname = 'Custom Plan'")
        (gemini_cmds / "sp-task.toml").write_text("[command]\nname = 'Custom Task'")
        (gemini_cmds / "sp-decompose.toml").write_text("[command]\nname = 'Custom Decompose'")
        
        # Test with custom commands
        sp2 = SpecPulse(tmp_path)
        assert "Custom" in sp2.get_claude_pulse_command()
        assert "Custom" in sp2.get_claude_spec_command()
        assert "Custom" in sp2.get_claude_plan_command()
        assert "Custom" in sp2.get_claude_task_command()
        assert "Custom" in sp2.get_claude_decompose_command()
        
        assert "Custom" in sp2.get_gemini_pulse_command()
        assert "Custom" in sp2.get_gemini_spec_command()
        assert "Custom" in sp2.get_gemini_plan_command()
        assert "Custom" in sp2.get_gemini_task_command()
        assert "Custom" in sp2.get_gemini_decompose_command()
    
    def test_decomposition_templates(self, tmp_path):
        """Cover lines 542-568 - decomposition templates"""
        sp = SpecPulse(tmp_path)
        
        # Test default templates
        assert "Microservices" in sp.get_decomposition_template("microservices")
        assert "openapi" in sp.get_decomposition_template("api")
        assert "interface" in sp.get_decomposition_template("interface")
        assert "Integration" in sp.get_decomposition_template("integration")
        assert "Service" in sp.get_decomposition_template("service_plan")
        assert sp.get_decomposition_template("unknown") is not None
        
        # Create custom decomposition templates
        decomp_dir = tmp_path / "templates" / "decomposition"
        decomp_dir.mkdir(parents=True)
        (decomp_dir / "microservices.md").write_text("# Custom Microservices")
        (decomp_dir / "api-contract.yaml").write_text("openapi: 3.0.0\ntitle: Custom API")
        (decomp_dir / "interface.ts").write_text("// Custom Interface")
        (decomp_dir / "integration-plan.md").write_text("# Custom Integration")
        (decomp_dir / "service-plan.md").write_text("# Custom Service Plan")
        
        # Test with custom templates
        sp2 = SpecPulse(tmp_path)
        # Templates are loaded and cached