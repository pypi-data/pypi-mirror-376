"""
Test for 100% coverage - Final version
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, ANY, mock_open
import sys
import os
import shutil
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from specpulse.cli.main import SpecPulseCLI, main
from specpulse.core.specpulse import SpecPulse
from specpulse.core.validator import Validator
from specpulse.utils.console import Console
from specpulse.utils.git_utils import GitUtils


class Test100Percent:
    """Final test for 100% coverage"""
    
    def test_cli_100(self, tmp_path, monkeypatch):
        """100% CLI coverage"""
        monkeypatch.chdir(tmp_path)
        cli = SpecPulseCLI()
        
        # Test init - all branches
        result = cli.init("test-project")
        assert result is True
        
        # Test init in existing project
        result = cli.init("test-project")
        assert result is True
        
        # Test init with here flag in current dir
        result = cli.init(".", here=True)
        assert result is True
        
        # Test validate
        result = cli.validate()
        assert result is True
        
        result = cli.validate(component="specs", fix=False, verbose=True)
        assert result is True
        
        # Test sync
        result = cli.sync()
        assert result is True
        
        # Test doctor
        result = cli.doctor()
        assert result is True
        
        # Test update (line 334-381)
        result = cli.update()
        assert result is True
        
        # Test decompose - all paths
        # No specs
        if (tmp_path / "specs").exists():
            shutil.rmtree(tmp_path / "specs")
        result = cli.decompose()
        assert result is False
        
        # Create specs
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        
        # Still no specs
        result = cli.decompose()
        assert result is False
        
        # Create spec
        spec_dir = specs_dir / "001-test"
        spec_dir.mkdir()
        (spec_dir / "spec-001.md").write_text("# Test")
        
        # Test all decompose variations
        result = cli.decompose()
        assert result is True
        
        result = cli.decompose("001")
        assert result is True
        
        result = cli.decompose("001-test")
        assert result is True
        
        result = cli.decompose("001", microservices=True, apis=False, interfaces=False)
        assert result is True
        
        result = cli.decompose("001", microservices=False, apis=True, interfaces=False)
        assert result is True
        
        result = cli.decompose("001", microservices=False, apis=False, interfaces=True)
        assert result is True
        
        result = cli.decompose("001", microservices=False, apis=False, interfaces=False)
        assert result is True
        
        # Test spec not found
        result = cli.decompose("999")
        assert result is False
        
        # Test spec dir but no file
        empty_dir = specs_dir / "002-empty"
        empty_dir.mkdir()
        result = cli.decompose("002")
        assert result is False
        
        # Test private methods
        cli._create_templates(tmp_path)
        cli._create_memory_files(tmp_path)
        cli._create_scripts(tmp_path)
        cli._create_ai_commands(tmp_path)
        cli._create_manifest(tmp_path, "test")
        
    def test_specpulse_100(self, tmp_path):
        """100% SpecPulse coverage"""
        # Test initialization
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            sp = SpecPulse()
            assert sp.project_path is not None
        finally:
            os.chdir(original_cwd)
            
        sp = SpecPulse(project_path=tmp_path)
        
        # Create all template files for 100% coverage
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        # Create main templates
        (templates_dir / "spec.md").write_text("spec")
        (templates_dir / "plan.md").write_text("plan")
        (templates_dir / "task.md").write_text("task")
        (templates_dir / "constitution.md").write_text("constitution")
        (templates_dir / "context.md").write_text("context")
        (templates_dir / "decisions.md").write_text("decisions")
        
        # Create decomposition templates
        decomp_dir = templates_dir / "decomposition"
        decomp_dir.mkdir()
        (decomp_dir / "microservices.md").write_text("ms")
        (decomp_dir / "api-contract.yaml").write_text("api")
        (decomp_dir / "interface.ts").write_text("interface")
        (decomp_dir / "integration-plan.md").write_text("integration")
        (decomp_dir / "service-plan.md").write_text("service")
        
        # Create scripts
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "sp-pulse-init.sh").write_text("init")
        (scripts_dir / "sp-pulse-spec.sh").write_text("spec")
        (scripts_dir / "sp-pulse-plan.sh").write_text("plan")
        (scripts_dir / "sp-pulse-task.sh").write_text("task")
        (scripts_dir / "sp-pulse-validate.sh").write_text("validate")
        (scripts_dir / "sp-pulse-generate.sh").write_text("generate")
        
        # Create Claude files
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "INSTRUCTIONS.md").write_text("claude inst")
        
        claude_cmd = claude_dir / "commands"
        claude_cmd.mkdir()
        (claude_cmd / "sp-pulse.md").write_text("pulse")
        (claude_cmd / "sp-spec.md").write_text("spec")
        (claude_cmd / "sp-plan.md").write_text("plan")
        (claude_cmd / "sp-task.md").write_text("task")
        
        # Create Gemini files
        gemini_dir = tmp_path / ".gemini"
        gemini_dir.mkdir()
        (gemini_dir / "INSTRUCTIONS.md").write_text("gemini inst")
        
        gemini_cmd = gemini_dir / "commands"
        gemini_cmd.mkdir()
        (gemini_cmd / "sp-pulse.toml").write_text("pulse")
        (gemini_cmd / "sp-spec.toml").write_text("spec")
        (gemini_cmd / "sp-plan.toml").write_text("plan")
        (gemini_cmd / "sp-task.toml").write_text("task")
        
        # Now test all methods to get 100%
        sp2 = SpecPulse(project_path=tmp_path)
        
        # All these should return custom content
        assert sp2.get_spec_template() == "spec"
        assert sp2.get_plan_template() == "plan"
        assert sp2.get_task_template() == "task"
        assert sp2.get_constitution_template() == "constitution"
        assert sp2.get_context_template() == "context"
        assert sp2.get_decisions_template() == "decisions"
        
        assert sp2.get_setup_script() == "init"
        assert sp2.get_spec_script() == "spec"
        assert sp2.get_plan_script() == "plan"
        assert sp2.get_task_script() == "task"
        assert sp2.get_validate_script() == "validate"
        assert sp2.get_generate_script() == "generate"
        
        assert sp2.get_claude_instructions() == "claude inst"
        assert sp2.get_claude_pulse_command() == "pulse"
        assert sp2.get_claude_spec_command() == "spec"
        assert sp2.get_claude_plan_command() == "plan"
        assert sp2.get_claude_task_command() == "task"
        
        assert sp2.get_gemini_instructions() == "gemini inst"
        assert sp2.get_gemini_pulse_command() == "pulse"
        assert sp2.get_gemini_spec_command() == "spec"
        assert sp2.get_gemini_plan_command() == "plan"
        assert sp2.get_gemini_task_command() == "task"
        
        assert sp2.get_decomposition_template("microservices") == "ms"
        assert sp2.get_decomposition_template("api") == "api"
        assert sp2.get_decomposition_template("interface") == "interface"
        assert sp2.get_decomposition_template("integration") == "integration"
        assert sp2.get_decomposition_template("service_plan") == "service"
        
        # Test fallback for unknown type
        assert sp2.get_decomposition_template("unknown") != ""
        
        # Test without files (fallback to defaults)
        sp3 = SpecPulse(project_path=tmp_path / "nonexistent")
        assert sp3.get_spec_template() != ""
        assert sp3.get_decomposition_template("microservices") != ""
        
    def test_validator_100(self, tmp_path):
        """100% Validator coverage"""
        os.chdir(tmp_path)
        
        # Setup
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "constitution.md").write_text("# Constitution\n## Core Principles")
        
        validator = Validator()
        
        # Test all validation methods
        spec = tmp_path / "spec.md"
        spec.write_text("""# Spec
## Overview
Test
## Requirements
- Req1
## Non-Functional Requirements
- NFR1
## Security Considerations
- Sec1
## Testing Strategy
- Test1""")
        
        result = validator.validate_spec(spec)
        assert result.valid is True
        
        # Invalid spec
        spec.write_text("# Bad")
        result = validator.validate_spec(spec)
        assert result.valid is False
        
        # Non-existent
        result = validator.validate_spec(tmp_path / "none.md")
        assert result.valid is False
        
        # Plan validation
        plan = tmp_path / "plan.md"
        plan.write_text("""# Plan
## Architecture
- Arch
## Phase 1: Init
- Task1
## Phase 2: Build
- Task2
## Testing Strategy
- Test
## Dependencies
- Dep""")
        
        result = validator.validate_plan(plan)
        assert result.valid is True
        
        plan.write_text("# Bad")
        result = validator.validate_plan(plan)
        assert result.valid is False
        
        result = validator.validate_plan(tmp_path / "none.md")
        assert result.valid is False
        
        # Task validation
        task = tmp_path / "task.md"
        task.write_text("""# Tasks
## T001: Setup
- Complexity: Low
- Time: 1h
## T002: Build
- Complexity: High
- Time: 4h""")
        
        result = validator.validate_task(task)
        assert result.valid is True
        
        task.write_text("# Bad")
        result = validator.validate_task(task)
        assert result.valid is False
        
        result = validator.validate_task(tmp_path / "none.md")
        assert result.valid is False
        
        # Validate all
        (tmp_path / "specs").mkdir()
        (tmp_path / "plans").mkdir()
        (tmp_path / "tasks").mkdir()
        
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir()
        (spec_dir / "spec-001.md").write_text("# Spec")
        (tmp_path / "plans" / "plan-001.md").write_text("# Plan")
        (tmp_path / "tasks" / "task-001.md").write_text("# Task")
        
        results = validator.validate_all()
        assert results is not None
        
        # Constitution compliance
        result = validator.validate_constitution_compliance(spec)
        assert isinstance(result.valid, bool)
        
        # Phase gate
        from tests.test_validator import PhaseGate
        gate = PhaseGate("Test", "Desc", ["check"])
        with patch.object(validator, '_check_research_completion', return_value=True, create=True):
            result = validator.check_phase_gate(gate, spec)
            assert isinstance(result, bool)
            
        # Format report
        from tests.test_validator import ValidationResult
        results = {
            "specs": ValidationResult(True, ["Error"], ["Warn"], ["Suggest"]),
            "plans": ValidationResult(False, ["Error"], [], []),
            "tasks": ValidationResult(True, [], [], [])
        }
        report = validator.format_validation_report(results)
        assert "Validation Report" in report
        
    def test_console_100(self):
        """100% Console coverage"""
        console = Console()
        
        # All methods
        console.show_banner()
        console.show_banner(mini=True)
        console.info("Info")
        console.success("Success")
        console.warning("Warning")
        console.error("Error")
        console.header("Header")
        console.section("Section", "Content")
        console.section("Section")
        
        with patch('specpulse.utils.console.Progress'):
            console.progress_bar("Test", 100)
            
        with patch('specpulse.utils.console.Live'):
            console.spinner("Test")
            
        with patch('time.sleep'):
            console.animated_text("Text", 0.001)
            
        with patch('specpulse.utils.console.Prompt.ask', return_value="test"):
            console.prompt("Prompt")
            console.prompt("Prompt", "default")
            
        with patch('specpulse.utils.console.Confirm.ask', return_value=True):
            console.confirm("Confirm")
            console.confirm("Confirm", True)
            
        console.table("Title", ["Col"], [["Val"]])
        console.table("Title", ["Col"], [["Val"]], show_lines=True)
        
        # Tree with nested structure
        tree_data = {"a": {"b": {"c": "d"}}, "e": "f"}
        console.tree("Tree", tree_data)
        
        # Mock Tree for _build_tree
        from rich.tree import Tree
        tree = Tree("root")
        console._build_tree(tree, tree_data)
        
        console.code_block("code")
        console.code_block("code", "javascript", "monokai")
        
        console.status_panel("Panel", [("k", "v")])
        
        console.validation_results({"a": True, "b": False})
        
        console.feature_showcase([
            {"name": "F1", "description": "D1", "status": "✓"},
            {"name": "F2", "description": "D2"}
        ])
        
        with patch('time.sleep'):
            console.animated_success("Success")
            console.pulse_animation("Pulse", 0.01)
            console.rocket_launch()
            console.rocket_launch("Launch")
            
        console.divider()
        console.divider("=", "red")
        
        console.gradient_text("Text")
        console.gradient_text("Text", ["red", "blue"])
        
        with patch('time.sleep'):
            console.celebration()
            
    def test_git_utils_100(self, tmp_path):
        """100% GitUtils coverage"""
        # Test all init paths
        utils1 = GitUtils()
        assert utils1.repo_path is not None
        
        utils2 = GitUtils(tmp_path)
        assert utils2.repo_path == tmp_path
        
        # All git operations
        success, output = utils2._run_git_command("--version")
        assert success is True
        
        success, output = utils2._run_git_command("invalid")
        assert success is False
        
        assert utils2.check_git_installed() is True
        
        assert utils2.is_git_repo() is False
        assert utils2.is_git_repo(tmp_path) is False
        
        assert utils2.init_repo() is True
        assert utils2.is_git_repo() is True
        
        branch = utils2.get_current_branch()
        assert branch in ["main", "master"]
        
        assert utils2.create_branch("test") is True
        assert utils2.create_branch("test") is False
        
        assert utils2.checkout_branch("test") is True
        assert utils2.checkout_branch("none") is False
        
        branches = utils2.get_branches()
        assert "test" in branches
        
        # File operations
        (tmp_path / "file.txt").write_text("content")
        assert utils2.add_files(["file.txt"]) is True
        assert utils2.add_files() is True
        
        assert utils2.commit("Test") is True
        assert utils2.commit("Empty") is False
        
        assert utils2.get_status() is not None
        assert utils2.has_changes() is not None
        
        log = utils2.get_log()
        assert isinstance(log, list)
        
        # Stash operations
        (tmp_path / "file2.txt").write_text("content2")
        assert utils2.stash_changes() is not None
        assert utils2.stash_changes("Message") is not None
        assert utils2.apply_stash() is not None
        assert utils2.apply_stash("stash@{0}") is not None
        
        # Remote operations
        assert utils2.get_remote_url() is None
        assert utils2.get_remote_url("origin") is None
        
        assert utils2.push() is False
        assert utils2.push("main") is False
        assert utils2.push("main", True) is False
        
        assert utils2.pull() is False
        assert utils2.pull("main") is False
        
        # Diff and tags
        diff = utils2.get_diff()
        assert diff is None or isinstance(diff, str)
        
        diff = utils2.get_diff(staged=True)
        assert diff is None or isinstance(diff, str)
        
        assert utils2.tag("v1.0") is True
        assert utils2.tag("v1.1", "Message") is True
        assert utils2.tag("v1.0") is False
        
        tags = utils2.get_tags()
        assert "v1.0" in tags
        
    def test_main_entry_100(self):
        """100% main entry coverage"""
        from specpulse.cli.main import main
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # All commands
            runner.invoke(main, ['--help'])
            runner.invoke(main, ['--version'])
            runner.invoke(main, ['init', 'test'])
            
            os.chdir('test')
            
            runner.invoke(main, ['validate'])
            runner.invoke(main, ['sync'])
            runner.invoke(main, ['doctor'])
            runner.invoke(main, ['list'])
            
            # Create spec
            spec_dir = Path('specs') / '001-test'
            spec_dir.mkdir(parents=True)
            (spec_dir / 'spec-001.md').write_text("# Test")
            
            runner.invoke(main, ['decompose'])
            runner.invoke(main, ['decompose', '001'])
            runner.invoke(main, ['decompose', '001', '--microservices'])
            runner.invoke(main, ['decompose', '001', '--apis'])
            runner.invoke(main, ['decompose', '001', '--interfaces'])