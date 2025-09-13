"""
Final test file to achieve 100% complete coverage
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
from specpulse.core.validator import Validator
from specpulse.utils.console import Console
from specpulse.utils.git_utils import GitUtils


class TestCLI100Complete:
    """Complete CLI coverage - all remaining lines"""
    
    def test_cli_lines_236_237_242(self, tmp_path, monkeypatch):
        """Cover validation component handling"""
        monkeypatch.chdir(tmp_path)
        cli = SpecPulseCLI()
        cli.init("test")
        os.chdir(tmp_path / "test")
        
        # Line 236-237: validate specs
        with patch.object(cli, 'console'):
            result = cli.validate(component="specs")
            # Returns False when no specs exist
        
        # Line 242: unknown component
        with patch.object(cli, 'console'):
            result = cli.validate(component="invalid_component")
            assert result is False
    
    def test_cli_line_274(self):
        """Cover update method"""
        cli = SpecPulseCLI()
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = cli.update()
            assert result is True
    
    def test_cli_lines_336_381(self, tmp_path):
        """Cover private helper methods"""
        cli = SpecPulseCLI()
        
        # _create_config
        config = cli._create_config("test")
        assert "project_name" in config
        
        # _create_scripts
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        cli._create_scripts(scripts_dir)
        assert len(list(scripts_dir.glob("*.sh"))) > 0
        
        # _create_templates
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        cli._create_templates(templates_dir)
        assert (templates_dir / "spec.md").exists()
        
        # _create_memory_files
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        cli._create_memory_files(memory_dir)
        assert (memory_dir / "constitution.md").exists()
        
        # _create_ai_commands
        cli._create_ai_commands(tmp_path)
        assert (tmp_path / ".claude").exists()
        
        # _create_pulse_manifest
        cli._create_pulse_manifest(tmp_path)
        assert (tmp_path / "PULSE.md").exists()
        
        # _show_init_summary
        with patch.object(cli.console, 'celebration'):
            cli._show_init_summary("test")
        
        # _generate_script_files
        cli._generate_script_files(scripts_dir)
    
    def test_cli_lines_385_413(self, tmp_path, monkeypatch):
        """Cover decompose method entry"""
        monkeypatch.chdir(tmp_path)
        cli = SpecPulseCLI()
        cli.init("test")
        os.chdir(tmp_path / "test")
        
        # No specs directory
        shutil.rmtree(tmp_path / "test" / "specs")
        result = cli.decompose()
        assert result is False
        
        # Empty specs directory
        (tmp_path / "test" / "specs").mkdir()
        result = cli.decompose()
        assert result is False
        
        # With spec
        spec_dir = tmp_path / "test" / "specs" / "001-test"
        spec_dir.mkdir()
        (spec_dir / "spec.md").write_text("# Spec")
        
        with patch.object(cli, '_parse_spec_content', return_value={"title": "Test"}):
            with patch.object(cli, '_generate_microservices'):
                result = cli.decompose("001")
                assert result is True
    
    def test_cli_lines_617_738(self, tmp_path):
        """Cover decompose helper methods"""
        cli = SpecPulseCLI()
        spec_dir = tmp_path / "spec"
        spec_dir.mkdir()
        
        # _generate_microservices
        cli._generate_microservices(spec_dir, {"title": "Test"})
        
        # _generate_api_contracts
        cli._generate_api_contracts(spec_dir, {"services": []})
        
        # _generate_interfaces
        cli._generate_interfaces(spec_dir, {"services": []})
        
        # _parse_spec_content
        content = cli._parse_spec_content("# Spec\n## Requirements\nTest")
        
        # _analyze_domain_boundaries
        boundaries = cli._analyze_domain_boundaries({})
        
        # _extract_services
        services = cli._extract_services({})
        
        # _generate_service_contracts
        contracts = cli._generate_service_contracts([])
        
        # _create_interface_definitions
        interfaces = cli._create_interface_definitions([])
    
    def test_cli_lines_743_806(self):
        """Cover main CLI entry"""
        runner = CliRunner()
        
        # Test help
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        
        # Test version
        result = runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        
        with runner.isolated_filesystem():
            # Test init
            result = runner.invoke(main, ['init', 'test'])
            assert result.exit_code == 0
            
            os.chdir('test')
            
            # Test all commands
            result = runner.invoke(main, ['validate'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['sync'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['doctor'])
            assert result.exit_code == 0
            
            # Create spec for decompose
            spec_dir = Path('specs') / '001-test'
            spec_dir.mkdir(parents=True, exist_ok=True)
            (spec_dir / 'spec.md').write_text("# Test")
            
            result = runner.invoke(main, ['decompose', '001'])
            assert result.exit_code == 0


class TestSpecPulse100Complete:
    """Complete SpecPulse core coverage"""
    
    def test_all_lines(self, tmp_path):
        """Cover all remaining lines in specpulse.py"""
        # Lines 25-32: initialization
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            sp = SpecPulse()
            assert sp.project_path == tmp_path
        finally:
            os.chdir(original_cwd)
        
        sp = SpecPulse(tmp_path)
        
        # Lines 38-39, 46-47, 130-131, 333: template checks
        templates_dir = tmp_path / "templates"
        
        # Test without custom templates (use defaults)
        assert "SpecPulse" in sp.spec_template
        assert "SpecPulse" in sp.plan_template
        assert "SpecPulse" in sp.task_template
        assert "SpecPulse" in sp.constitution_template
        assert "Context" in sp.context_template
        assert "Decision" in sp.decisions_template
        
        # Create custom templates
        templates_dir.mkdir()
        (templates_dir / "spec.md").write_text("Custom")
        (templates_dir / "plan.md").write_text("Custom")
        (templates_dir / "task.md").write_text("Custom")
        (templates_dir / "constitution.md").write_text("Custom")
        (templates_dir / "context.md").write_text("Custom")
        (templates_dir / "decisions.md").write_text("Custom")
        
        # Reinitialize with custom templates
        sp = SpecPulse(tmp_path)
        
        # Lines 423, 503, 577, 597-602, 651-656, 694-699, 741-746: scripts
        scripts_dir = tmp_path / "scripts"
        
        # Test without custom scripts (use defaults)
        assert "#!/bin/bash" in sp.setup_script
        assert "#!/bin/bash" in sp.spec_script
        assert "#!/bin/bash" in sp.plan_script
        assert "#!/bin/bash" in sp.task_script
        assert "#!/bin/bash" in sp.validate_script
        assert "#!/bin/bash" in sp.generate_script
        assert "#!/bin/bash" in sp.decompose_script
        
        # Create custom scripts
        scripts_dir.mkdir()
        (scripts_dir / "sp-pulse-init.sh").write_text("custom")
        (scripts_dir / "sp-pulse-spec.sh").write_text("custom")
        (scripts_dir / "sp-pulse-plan.sh").write_text("custom")
        (scripts_dir / "sp-pulse-task.sh").write_text("custom")
        (scripts_dir / "sp-pulse-validate.sh").write_text("custom")
        (scripts_dir / "sp-pulse-generate.sh").write_text("custom")
        (scripts_dir / "sp-pulse-decompose.sh").write_text("custom")
        
        # Reinitialize with custom scripts
        sp = SpecPulse(tmp_path)
        
        # Test all getters work
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
        
        # Lines 556-568: decomposition templates
        decomp_dir = templates_dir / "decomposition"
        
        # Test without custom decomposition templates
        assert sp.get_decomposition_template("microservices") is not None
        assert sp.get_decomposition_template("api") is not None
        assert sp.get_decomposition_template("interface") is not None
        assert sp.get_decomposition_template("integration") is not None
        assert sp.get_decomposition_template("service_plan") is not None
        assert sp.get_decomposition_template("unknown") is not None
        
        # Create custom decomposition templates
        decomp_dir.mkdir()
        (decomp_dir / "microservices.md").write_text("custom")
        (decomp_dir / "api-contract.yaml").write_text("custom")
        (decomp_dir / "interface.ts").write_text("custom")
        (decomp_dir / "integration-plan.md").write_text("custom")
        (decomp_dir / "service-plan.md").write_text("custom")
        
        # Reinitialize
        sp = SpecPulse(tmp_path)
        
        # Lines 791, 842, 870: AI instructions
        claude_dir = tmp_path / ".claude"
        gemini_dir = tmp_path / ".gemini"
        
        # Test without custom instructions
        assert sp.get_claude_instructions() is not None
        assert sp.get_gemini_instructions() is not None
        assert sp.get_claude_decompose_instructions() is not None
        
        # Create custom instructions
        claude_dir.mkdir()
        (claude_dir / "INSTRUCTIONS.md").write_text("custom")
        (claude_dir / "DECOMPOSE_INSTRUCTIONS.md").write_text("custom")
        gemini_dir.mkdir()
        (gemini_dir / "INSTRUCTIONS.md").write_text("custom")
        
        # Reinitialize
        sp = SpecPulse(tmp_path)
        
        # Lines 953-1018: command templates
        claude_cmds = claude_dir / "commands"
        gemini_cmds = gemini_dir / "commands"
        
        # Test without custom commands
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
        
        # Create custom commands
        claude_cmds.mkdir()
        (claude_cmds / "sp-pulse.md").write_text("custom")
        (claude_cmds / "sp-spec.md").write_text("custom")
        (claude_cmds / "sp-plan.md").write_text("custom")
        (claude_cmds / "sp-task.md").write_text("custom")
        (claude_cmds / "sp-decompose.md").write_text("custom")
        
        gemini_cmds.mkdir()
        (gemini_cmds / "sp-pulse.toml").write_text("custom")
        (gemini_cmds / "sp-spec.toml").write_text("custom")
        (gemini_cmds / "sp-plan.toml").write_text("custom")
        (gemini_cmds / "sp-task.toml").write_text("custom")
        (gemini_cmds / "sp-decompose.toml").write_text("custom")
        
        # Reinitialize and test
        sp = SpecPulse(tmp_path)
        
        # Verify all work
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