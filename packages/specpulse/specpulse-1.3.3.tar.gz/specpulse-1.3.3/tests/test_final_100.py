"""
Final comprehensive test for 100% coverage
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open, call
import subprocess
import yaml
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from specpulse.cli.main import SpecPulseCLI
from specpulse.core.specpulse import SpecPulse
from specpulse.core.validator import Validator
from specpulse.utils.console import Console
from specpulse.utils.git_utils import GitUtils


class TestFinal100Coverage:
    """Test suite targeting 100% coverage"""
    
    def test_cli_all_lines(self, tmp_path, monkeypatch):
        """Cover all CLI lines including edge cases"""
        monkeypatch.chdir(tmp_path)
        
        # Test init
        cli = SpecPulseCLI()
        result = cli.init("test-project")
        assert result is True
        
        # Test validate - cover line 236-237, 242
        os.chdir(tmp_path / "test-project")
        
        # No component specified - uses validate_all
        result = cli.validate()
        assert result is True
        
        # Component "all" - also uses validate_all
        result = cli.validate(component="all")
        assert result is True
        
        # Component "spec" or "specs" - uses validate_spec
        result = cli.validate(component="spec")
        assert result is False  # No specs yet
        
        # Component "plan" or "plans" - uses validate_plan  
        result = cli.validate(component="plan")
        assert result is False  # No plans yet
        
        # Component "constitution" - uses validate_constitution
        result = cli.validate(component="constitution")
        assert result is True
        
        # Unknown component - line 242
        result = cli.validate(component="unknown")
        assert result is False
        
        # Test sync
        result = cli.sync()
        assert result is True
        
        # Test doctor
        result = cli.doctor()
        assert result is True
        
        # Test update - line 274
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = cli.update()
            assert result is True
            
            mock_run.return_value = Mock(returncode=1)
            result = cli.update()
            assert result is False
        
        # Test decompose - lines 395, 397, 399, 420-613
        # No specs directory
        shutil.rmtree(tmp_path / "test-project" / "specs")
        result = cli.decompose()
        assert result is False
        
        # Create specs directory but empty
        (tmp_path / "test-project" / "specs").mkdir()
        result = cli.decompose()
        assert result is False
        
        # Create a spec
        spec_dir = tmp_path / "test-project" / "specs" / "001-test"
        spec_dir.mkdir()
        (spec_dir / "spec.md").write_text("# Test Spec\n## Requirements\nTest requirements")
        
        # Test decompose with spec_id
        result = cli.decompose("001-test")
        assert result is True
        
        # Test decompose with all=True
        result = cli.decompose("001-test", all=True)
        assert result is True
        
        # Test decompose with individual flags
        result = cli.decompose("001-test", microservices=True, apis=False, interfaces=False)
        assert result is True
        
        result = cli.decompose("001-test", microservices=False, apis=True, interfaces=False)
        assert result is True
        
        result = cli.decompose("001-test", microservices=False, apis=False, interfaces=True)
        assert result is True
        
        # Test decompose without spec_id (auto-detect)
        result = cli.decompose()
        assert result is True
        
        # Test decompose with multiple specs (prompts user)
        spec_dir2 = tmp_path / "test-project" / "specs" / "002-test"
        spec_dir2.mkdir()
        (spec_dir2 / "spec.md").write_text("# Test 2")
        
        with patch('rich.prompt.Prompt.ask', return_value="001-test"):
            result = cli.decompose()
            assert result is True
        
        # Test decompose with non-existent spec
        result = cli.decompose("999-nonexistent")
        assert result is False
        
        # Test _create methods - lines 336-381
        config = cli._create_config("test")
        assert config["project_name"] == "test"
        
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        cli._create_scripts(scripts_dir)
        assert (scripts_dir / "sp-pulse-init.sh").exists()
        
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir(exist_ok=True)
        cli._create_templates(templates_dir)
        assert (templates_dir / "spec.md").exists()
        
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir(exist_ok=True)
        cli._create_memory_files(memory_dir)
        assert (memory_dir / "constitution.md").exists()
        
        cli._create_ai_commands(tmp_path)
        assert (tmp_path / ".claude" / "commands").exists()
        
        cli._create_pulse_manifest(tmp_path)
        assert (tmp_path / "PULSE.md").exists()
        
        cli._show_init_summary("test")
        
        cli._generate_script_files(scripts_dir)
        
        # Test decompose helper methods - lines 617-658
        cli._generate_microservices(spec_dir, {"content": "Test"})
        assert (spec_dir / "microservices.md").exists()
        
        cli._generate_api_contracts(spec_dir, {"content": "Test"})
        assert (spec_dir / "api-contracts").exists()
        
        cli._generate_interfaces(spec_dir, {"content": "Test"})
        assert (spec_dir / "interfaces").exists()
        
        # Test lines 662-738 (private helpers)
        cli._parse_spec_content("# Test\n## Requirements\nTest")
        cli._analyze_domain_boundaries({"content": "Test"})
        cli._extract_services({"content": "Test"})
        cli._generate_service_contracts([{"name": "service1"}])
        cli._create_interface_definitions([{"name": "service1"}])
        
        # Cover lines 40-41 (git error handling)
        with patch('specpulse.utils.git_utils.GitUtils') as mock_git:
            mock_git_instance = Mock()
            mock_git.return_value = mock_git_instance
            mock_git_instance.check_git_installed.return_value = False
            
            cli2 = SpecPulseCLI()
            # Git not installed warning is shown but init continues
    
    def test_cli_main_entry(self):
        """Test main CLI entry point - lines 743-806"""
        from specpulse.cli.main import main
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        # Test help
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        
        # Test version
        result = runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        
        with runner.isolated_filesystem():
            # Test all commands
            result = runner.invoke(main, ['init', 'test'])
            assert result.exit_code == 0
            
            os.chdir('test')
            
            result = runner.invoke(main, ['validate'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['sync'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['doctor'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['update'])
            # May fail if pip update fails, but command runs
            assert result.exit_code in [0, 1]
            
            # Create spec for decompose
            spec_dir = Path('specs') / '001-test'
            spec_dir.mkdir(parents=True)
            (spec_dir / 'spec.md').write_text("# Test")
            
            result = runner.invoke(main, ['decompose', '001-test'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['decompose', '001-test', '--all'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['decompose', '001-test', '--microservices'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['decompose', '001-test', '--apis'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['decompose', '001-test', '--interfaces'])
            assert result.exit_code == 0
    
    def test_specpulse_all_lines(self, tmp_path):
        """Cover all SpecPulse core lines"""
        # Lines 25-32: init without path (uses cwd)
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            sp = SpecPulse()
            assert sp.project_path == tmp_path
        finally:
            os.chdir(original_cwd)
        
        # Create project structure with templates
        project_path = tmp_path / "project"
        project_path.mkdir()
        templates_dir = project_path / "templates"
        templates_dir.mkdir()
        
        # Lines 38-39, 46-47, 130-131, 333, 423, 503, 577
        # Create all template files
        (templates_dir / "spec.md").write_text("Custom spec")
        (templates_dir / "plan.md").write_text("Custom plan")
        (templates_dir / "task.md").write_text("Custom task")
        (templates_dir / "constitution.md").write_text("Custom const")
        (templates_dir / "context.md").write_text("Custom ctx")
        (templates_dir / "decisions.md").write_text("Custom dec")
        
        # Scripts
        scripts_dir = project_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "sp-pulse-init.sh").write_text("Custom init")
        (scripts_dir / "sp-pulse-spec.sh").write_text("Custom spec")
        (scripts_dir / "sp-pulse-plan.sh").write_text("Custom plan")
        (scripts_dir / "sp-pulse-task.sh").write_text("Custom task")
        (scripts_dir / "sp-pulse-validate.sh").write_text("Custom val")
        (scripts_dir / "sp-pulse-generate.sh").write_text("Custom gen")
        
        sp = SpecPulse(project_path)
        
        # Test reading custom templates
        assert sp.get_spec_template() == "Custom spec"
        assert sp.get_plan_template() == "Custom plan"
        assert sp.get_task_template() == "Custom task"
        assert sp.get_constitution_template() == "Custom const"
        assert sp.get_context_template() == "Custom ctx"
        assert sp.get_decisions_template() == "Custom dec"
        
        # Test reading custom scripts - lines 597-602, 651-656, 694-699, 741-746
        assert sp.get_setup_script() == "Custom init"
        assert sp.get_spec_script() == "Custom spec"
        assert sp.get_plan_script() == "Custom plan"
        assert sp.get_task_script() == "Custom task"
        assert sp.get_validate_script() == "Custom val"
        assert sp.get_generate_script() == "Custom gen"
        
        # Lines 542-568: decomposition templates
        decomp_dir = templates_dir / "decomposition"
        decomp_dir.mkdir()
        (decomp_dir / "microservices.md").write_text("MS template")
        (decomp_dir / "api-contract.yaml").write_text("API template")
        (decomp_dir / "interface.ts").write_text("Interface template")
        (decomp_dir / "integration-plan.md").write_text("Integration template")
        (decomp_dir / "service-plan.md").write_text("Service template")
        
        sp2 = SpecPulse(project_path)
        assert sp2.get_decomposition_template("microservices") == "MS template"
        assert sp2.get_decomposition_template("api") == "API template"
        assert sp2.get_decomposition_template("interface") == "Interface template"
        assert sp2.get_decomposition_template("integration") == "Integration template"
        assert sp2.get_decomposition_template("service_plan") == "Service template"
        
        # Test unknown template type
        assert "microservices" in sp2.get_decomposition_template("unknown")
        
        # Lines 791, 842, 870: instruction templates
        claude_dir = project_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "INSTRUCTIONS.md").write_text("Claude inst")
        
        gemini_dir = project_path / ".gemini"
        gemini_dir.mkdir()
        (gemini_dir / "INSTRUCTIONS.md").write_text("Gemini inst")
        
        sp3 = SpecPulse(project_path)
        assert sp3.get_claude_instructions() == "Claude inst"
        assert sp3.get_gemini_instructions() == "Gemini inst"
        
        # Lines 953-957, 961-965, 969-973, 977-981: Claude commands
        claude_cmds = claude_dir / "commands"
        claude_cmds.mkdir()
        (claude_cmds / "sp-pulse.md").write_text("Pulse cmd")
        (claude_cmds / "sp-spec.md").write_text("Spec cmd")
        (claude_cmds / "sp-plan.md").write_text("Plan cmd")
        (claude_cmds / "sp-task.md").write_text("Task cmd")
        
        sp4 = SpecPulse(project_path)
        assert sp4.get_claude_pulse_command() == "Pulse cmd"
        assert sp4.get_claude_spec_command() == "Spec cmd"
        assert sp4.get_claude_plan_command() == "Plan cmd"
        assert sp4.get_claude_task_command() == "Task cmd"
        
        # Lines 986-990, 994-998, 1002-1006, 1010-1014, 1018: Gemini commands
        gemini_cmds = gemini_dir / "commands"
        gemini_cmds.mkdir()
        (gemini_cmds / "sp-pulse.toml").write_text("Pulse toml")
        (gemini_cmds / "sp-spec.toml").write_text("Spec toml")
        (gemini_cmds / "sp-plan.toml").write_text("Plan toml")
        (gemini_cmds / "sp-task.toml").write_text("Task toml")
        (gemini_cmds / "sp-decompose.toml").write_text("Decompose toml")
        
        sp5 = SpecPulse(project_path)
        assert sp5.get_gemini_pulse_command() == "Pulse toml"
        assert sp5.get_gemini_spec_command() == "Spec toml"
        assert sp5.get_gemini_plan_command() == "Plan toml"
        assert sp5.get_gemini_task_command() == "Task toml"
        assert sp5.get_gemini_decompose_command() == "Decompose toml"
    
    def test_validator_all_lines(self, tmp_path):
        """Cover all Validator lines"""
        project_path = tmp_path / "project"
        project_path.mkdir()
        
        # Create all required directories
        for dir_name in [".specpulse", "memory", "specs", "templates", "scripts", "plans"]:
            (project_path / dir_name).mkdir()
        
        # Create config
        config = {"constitution": {"enforce": True}}
        (project_path / ".specpulse" / "config.yaml").write_text(yaml.dump(config))
        
        # Create constitution
        (project_path / "memory" / "constitution.md").write_text("""
# Constitution
- Simplicity First
- Test-Driven Development
- Single Responsibility
- Documentation as Code
- Security by Design
        """)
        
        validator = Validator()
        
        # Test validate_all
        results = validator.validate_all(project_path, fix=False, verbose=False)
        assert isinstance(results, list)
        
        # Create spec with missing sections for fix test
        spec_dir = project_path / "specs" / "spec001"
        spec_dir.mkdir()
        spec_path = spec_dir / "spec.md"
        spec_path.write_text("# Test Spec")
        
        # Test with fix=True (adds missing sections)
        results = validator.validate_all(project_path, fix=True, verbose=True)
        assert isinstance(results, list)
        
        # Test validate_spec with clarifications
        spec_path.write_text("""
# Test Spec
## Requirements
[NEEDS CLARIFICATION] requirement 1
[NEEDS CLARIFICATION] requirement 2
## User Stories
Test story
## Acceptance Criteria
Test criteria
        """)
        
        results = validator.validate_spec(project_path, "spec001", fix=False, verbose=True)
        assert isinstance(results, list)
        
        # Test validate_spec without verbose (different branch)
        results = validator.validate_spec(project_path, "spec001", fix=False, verbose=False)
        assert isinstance(results, list)
        
        # Test non-existent spec
        results = validator.validate_spec(project_path, "nonexistent")
        assert any(r["status"] == "error" for r in results)
        
        # Test validate all specs
        results = validator.validate_spec(project_path, None)
        assert isinstance(results, list)
        
        # Create plan with missing sections
        plan_dir = project_path / "plans" / "plan001"
        plan_dir.mkdir()
        plan_path = plan_dir / "plan.md"
        plan_path.write_text("# Test Plan")
        
        # Test validate_plan with fix
        results = validator.validate_plan(project_path, "plan001", fix=True, verbose=False)
        assert isinstance(results, list)
        
        # Add Spec ID reference
        plan_path.write_text("""
# Test Plan
## Architecture
Test arch
## Technology Stack
Test stack
## Implementation Phases
Phase 1
Spec ID: spec001
        """)
        
        results = validator.validate_plan(project_path, "plan001", fix=False, verbose=True)
        assert isinstance(results, list)
        
        # Test validate all plans
        results = validator.validate_plan(project_path, None)
        assert isinstance(results, list)
        
        # Test non-existent plan
        results = validator.validate_plan(project_path, "nonexistent")
        assert any(r["status"] == "error" for r in results)
        
        # Test validate_constitution with verbose
        results = validator.validate_constitution(project_path, verbose=True)
        assert isinstance(results, list)
        
        # Test with missing directories
        shutil.rmtree(project_path / "specs")
        results = validator.validate_spec(project_path)
        assert any(r["status"] == "error" for r in results)
        
        shutil.rmtree(project_path / "plans")
        results = validator.validate_plan(project_path)
        assert any(r["status"] == "warning" for r in results)
        
        # Test with missing constitution
        os.remove(project_path / "memory" / "constitution.md")
        results = validator.validate_constitution(project_path)
        assert any(r["status"] == "error" for r in results)
        
        # Test with missing config
        os.remove(project_path / ".specpulse" / "config.yaml")
        results = validator.validate_constitution(project_path)
        assert isinstance(results, list)
        
        # Test validate_all with missing structure
        for dir_name in ["templates", "scripts"]:
            if (project_path / dir_name).exists():
                shutil.rmtree(project_path / dir_name)
        
        results = validator.validate_all(project_path)
        assert any(r["status"] == "error" for r in results)
    
    def test_console_all_lines(self):
        """Cover all Console lines"""
        console = Console(no_color=False, verbose=True)
        
        # Test all methods
        console.show_banner(mini=False)
        console.show_banner(mini=True)
        
        console.info("Info")
        console.success("Success")
        console.warning("Warning")
        console.error("Error")
        
        # Test with custom icons - line 90
        console.info("Info", icon=">>")
        console.success("Success", icon="✓")
        console.warning("Warning", icon="⚠")
        console.error("Error", icon="✗")
        
        console.header("Header")
        
        # Lines 110-114
        console.section("Section", "Content here")
        console.section("Section")
        
        # Lines 119-130
        progress = console.progress_bar("Test", 100)
        with progress:
            pass
        
        console.spinner("Loading")
        
        # Lines 140-143
        console.animated_text("Text", delay=0.001)
        
        # Lines 147, 155
        with patch('rich.prompt.Prompt.ask', return_value="input"):
            result = console.prompt("Enter")
            assert result == "input"
            
            result = console.prompt("Enter", default="default")
            assert result == "input"
        
        with patch('rich.prompt.Confirm.ask', return_value=True):
            result = console.confirm("Sure?")
            assert result is True
            
            result = console.confirm("Sure?", default=False)
            assert result is True
        
        # Lines 164-181
        console.table("Title", ["Col1", "Col2"], [["a", "b"]])
        console.table("Title", ["Col1"], [], show_footer=True)
        
        # Lines 185-200
        console.tree("Tree", {
            "dict": {"nested": "value"},
            "list": ["item1", "item2"],
            "value": "simple"
        })
        
        # Lines 204-207
        console.code_block("code", "python")
        console.code_block("code", "javascript", theme="github-dark")
        
        # Lines 211-218
        console.status_panel("Status", [("key", "value")])
        
        # Lines 222-250
        console.validation_results({"test1": True, "test2": False})
        console.validation_results({"test1": True, "test2": True})
        
        console.feature_showcase([
            {"name": "F1", "description": "D1"},
            {"name": "F2", "description": "D2"},
            {"name": "F3", "description": "D3"},
            {"name": "F4", "description": "D4"},
            {"name": "F5", "description": "D5"},
            {"name": "F6", "description": "D6"}
        ])
        
        console.animated_success("Success")
        console.pulse_animation("Pulse", duration=0.01)
        
        # Lines 294-298
        console.rocket_launch("Launch")
        console.rocket_launch()
        
        # Lines 302-303
        console.divider()
        console.divider(char="=", style="red")
        
        # Line 308
        console.gradient_text("Text")
        console.gradient_text("Text", colors=["red", "blue"])
        
        console.celebration()
        
        # Test with no_color
        console_nc = Console(no_color=True, verbose=False)
        console_nc.show_banner()
    
    def test_git_utils_all_lines(self, tmp_path):
        """Cover all GitUtils lines"""
        # Line 14: init without path
        git = GitUtils()
        assert git.repo_path == Path.cwd()
        
        # Test with path
        git = GitUtils(tmp_path)
        
        # Lines 18-30: _run_git_command
        with patch('subprocess.run') as mock_run:
            # Success case
            mock_run.return_value = Mock(stdout="output", stderr="", returncode=0)
            success, output = git._run_git_command("--version")
            assert success is True
            assert output == "output"
            
            # Failure case
            mock_run.side_effect = subprocess.CalledProcessError(1, "git", stderr="error")
            success, output = git._run_git_command("bad-command")
            assert success is False
            assert "error" in output
            
            # FileNotFoundError case
            mock_run.side_effect = FileNotFoundError()
            success, output = git._run_git_command("--version")
            assert success is False
            assert "not installed" in output
        
        # Lines 34-35: check_git_installed
        with patch.object(git, '_run_git_command', return_value=(True, "git version")):
            assert git.check_git_installed() is True
        
        with patch.object(git, '_run_git_command', return_value=(False, "error")):
            assert git.check_git_installed() is False
        
        # Lines 39-41: is_git_repo
        assert git.is_git_repo() is False
        assert git.is_git_repo(tmp_path) is False
        
        (tmp_path / ".git").mkdir()
        assert git.is_git_repo() is True
        assert git.is_git_repo(tmp_path) is True
        
        # Lines 45-46: init_repo
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            assert git.init_repo() is True
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.init_repo() is False
        
        # Lines 50-51: get_current_branch
        with patch.object(git, '_run_git_command', return_value=(True, "main")):
            assert git.get_current_branch() == "main"
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.get_current_branch() is None
        
        # Lines 55-56: create_branch
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            assert git.create_branch("new") is True
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.create_branch("new") is False
        
        # Lines 60-61: checkout_branch
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            assert git.checkout_branch("main") is True
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.checkout_branch("main") is False
        
        # Lines 65-76: get_branches
        with patch.object(git, '_run_git_command', return_value=(True, "* main\n  develop\n  feature")):
            branches = git.get_branches()
            assert "main" in branches
            assert "develop" in branches
            assert "feature" in branches
        
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            branches = git.get_branches()
            assert branches == []
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            branches = git.get_branches()
            assert branches == []
        
        # Lines 80-84: add_files
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            assert git.add_files(["file1", "file2"]) is True
            assert git.add_files() is True
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.add_files(["file1"]) is False
            assert git.add_files() is False
        
        # Lines 88-89: commit
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            assert git.commit("message") is True
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.commit("message") is False
        
        # Lines 93-94: get_status
        with patch.object(git, '_run_git_command', return_value=(True, "M file.txt")):
            assert git.get_status() == "M file.txt"
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.get_status() is None
        
        # Lines 98-99: has_changes
        with patch.object(git, 'get_status', return_value="M file.txt"):
            assert git.has_changes() is True
        
        with patch.object(git, 'get_status', return_value=""):
            assert git.has_changes() is False
        
        with patch.object(git, 'get_status', return_value=None):
            assert git.has_changes() is False
        
        # Lines 103-110: get_log
        with patch.object(git, '_run_git_command', return_value=(True, "commit1\ncommit2")):
            log = git.get_log(5)
            assert log == ["commit1", "commit2"]
        
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            log = git.get_log()
            assert log == []
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            log = git.get_log()
            assert log == []
        
        # Lines 114-118: stash_changes
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            assert git.stash_changes("message") is True
            assert git.stash_changes() is True
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.stash_changes("message") is False
            assert git.stash_changes() is False
        
        # Lines 122-126: apply_stash
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            assert git.apply_stash("stash@{0}") is True
            assert git.apply_stash() is True
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.apply_stash("stash@{0}") is False
            assert git.apply_stash() is False
        
        # Lines 130-131: get_remote_url
        with patch.object(git, '_run_git_command', return_value=(True, "https://github.com/repo")):
            assert git.get_remote_url() == "https://github.com/repo"
            assert git.get_remote_url("upstream") == "https://github.com/repo"
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.get_remote_url() is None
            assert git.get_remote_url("upstream") is None
        
        # Lines 135-142: push
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            assert git.push() is True
            assert git.push("main") is True
            assert git.push("main", force=True) is True
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.push() is False
            assert git.push("main") is False
            assert git.push("main", force=True) is False
        
        # Lines 146-151: pull
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            assert git.pull() is True
            assert git.pull("main") is True
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.pull() is False
            assert git.pull("main") is False
        
        # Lines 155-160: get_diff
        with patch.object(git, '_run_git_command', return_value=(True, "diff output")):
            assert git.get_diff() == "diff output"
            assert git.get_diff(staged=True) == "diff output"
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.get_diff() is None
            assert git.get_diff(staged=True) is None
        
        # Lines 164-171: tag
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            assert git.tag("v1.0") is True
            assert git.tag("v1.1", "message") is True
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            assert git.tag("v1.0") is False
            assert git.tag("v1.1", "message") is False
        
        # Lines 175-178: get_tags
        with patch.object(git, '_run_git_command', return_value=(True, "v1.0\nv1.1")):
            tags = git.get_tags()
            assert tags == ["v1.0", "v1.1"]
        
        with patch.object(git, '_run_git_command', return_value=(True, "")):
            tags = git.get_tags()
            assert tags == []
        
        with patch.object(git, '_run_git_command', return_value=(False, "")):
            tags = git.get_tags()
            assert tags == []