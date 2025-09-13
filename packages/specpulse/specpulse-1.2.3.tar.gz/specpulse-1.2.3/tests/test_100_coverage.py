"""
Additional tests to achieve 100% coverage
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import os
import yaml
import click
from click.testing import CliRunner

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from specpulse.cli.main import SpecPulseCLI, main
from specpulse.core.specpulse import SpecPulse
from specpulse.core.validator import Validator
from specpulse.utils.console import Console
from specpulse.utils.git_utils import GitUtils


class Test100Coverage:
    """Tests to reach 100% coverage"""
    
    def test_cli_main_function(self):
        """Test the main CLI entry point"""
        runner = CliRunner()
        
        # Test help
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        
        # Test version
        result = runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert '1.2.2' in result.output
        
    def test_cli_uncovered_methods(self, tmp_path, monkeypatch):
        """Test uncovered CLI methods"""
        monkeypatch.chdir(tmp_path)
        cli = SpecPulseCLI()
        
        # Initialize a project first
        cli.init(".", here=True)
        
        # Create more complex spec structure
        spec_dir1 = Path("specs") / "001-feature"
        spec_dir1.mkdir(parents=True)
        (spec_dir1 / "spec-001.md").write_text("# Feature 1")
        
        spec_dir2 = Path("specs") / "002-feature"
        spec_dir2.mkdir(parents=True)
        (spec_dir2 / "spec-001.md").write_text("# Feature 2")
        
        # Test decompose with hyphenated spec ID
        result = cli.decompose(spec_id="001-feature")
        assert result is True
        
        # Test decompose when spec doesn't exist
        result = cli.decompose(spec_id="999")
        assert result is False
        
        # Test decompose when spec directory exists but no spec file
        spec_dir3 = Path("specs") / "003-empty"
        spec_dir3.mkdir(parents=True)
        result = cli.decompose(spec_id="003")
        assert result is False
        
        # Test validate when missing constitution
        (Path("memory") / "constitution.md").unlink()
        result = cli.validate()
        assert result is True  # Still validates structure
        
        # Test sync when directories missing
        import shutil
        shutil.rmtree("templates")
        result = cli.sync()
        assert result is True
        
    def test_specpulse_edge_cases(self, tmp_path):
        """Test SpecPulse edge cases"""
        # Test with current directory
        sp = SpecPulse()
        assert sp.project_path is not None
        
        # Test templates from package resources
        sp = SpecPulse(project_path=tmp_path)
        
        # Create templates directory but no files
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        # These should fall back to package templates
        assert sp.get_spec_template() is not None
        assert sp.get_plan_template() is not None
        
        # Test decomposition with custom templates
        decomp_dir = templates_dir / "decomposition"
        decomp_dir.mkdir()
        
        # Test different template types
        for template_type in ["microservices", "api", "interface", "integration", "service_plan"]:
            template = sp.get_decomposition_template(template_type)
            assert template is not None
            
    def test_validator_uncovered(self, tmp_path):
        """Test uncovered Validator methods"""
        validator = Validator()
        
        # Test with empty files
        empty_spec = tmp_path / "empty_spec.md"
        empty_spec.write_text("")
        result = validator.validate_spec(empty_spec)
        assert result.valid is False
        
        empty_plan = tmp_path / "empty_plan.md"
        empty_plan.write_text("")
        result = validator.validate_plan(empty_plan)
        assert result.valid is False
        
        empty_task = tmp_path / "empty_task.md"
        empty_task.write_text("")
        result = validator.validate_task(empty_task)
        assert result.valid is False
        
        # Test with malformed files
        bad_spec = tmp_path / "bad_spec.md"
        bad_spec.write_text("Not a proper spec")
        result = validator.validate_spec(bad_spec)
        assert result.valid is False
        
        # Test phase gate checks
        from tests.test_validator import PhaseGate
        gate = PhaseGate("Test", "Description", ["check1", "check2"])
        
        # Mock the check methods
        with patch.object(validator, '_check_research_completion', return_value=True):
            with patch.object(validator, '_check_dependencies', return_value=True):
                result = validator.check_phase_gate(gate, tmp_path / "spec.md")
                assert isinstance(result, bool)
                
    def test_console_uncovered(self):
        """Test uncovered Console methods"""
        console = Console(no_color=True, verbose=True)
        
        # Test with no_color and verbose
        console.info("Test", icon="[*]")
        console.success("Test", icon="[+]")
        console.warning("Test", icon="[!]")
        console.error("Test", icon="[X]")
        console.header("Test", style="red")
        
        # Test section with content
        console.section("Title", "Content here")
        
        # Test validation results with failures
        console.validation_results({"test1": True, "test2": False})
        
        # Test feature showcase with multiple features
        features = [
            {"name": "Feature 1", "description": "Desc 1", "status": "active"},
            {"name": "Feature 2", "description": "Desc 2"},
        ]
        console.feature_showcase(features)
        
        # Test gradient with custom colors
        console.gradient_text("Test", colors=["red", "blue"])
        
        # Test code block with different themes
        console.code_block("code", language="javascript", theme="github-dark")
        
    def test_git_utils_uncovered(self, tmp_path):
        """Test uncovered GitUtils methods"""
        utils = GitUtils()
        
        # Test with current directory (which is a git repo)
        assert utils.repo_path is not None
        
        # Test specific path operations
        utils2 = GitUtils(tmp_path)
        utils2.init_repo()
        
        # Test is_git_repo with specific path
        result = utils2.is_git_repo(tmp_path)
        assert result is True
        
        # Test stash with message
        (tmp_path / "file.txt").write_text("content")
        utils2.add_files()
        result = utils2.stash_changes("Custom stash message")
        assert isinstance(result, bool)
        
        # Test apply_stash with stash ID
        result = utils2.apply_stash("stash@{0}")
        assert isinstance(result, bool)
        
        # Test push with branch and force
        result = utils2.push(branch="main", force=True)
        assert isinstance(result, bool)
        
        # Test pull with branch
        result = utils2.pull(branch="main")
        assert isinstance(result, bool)
        
        # Test tag with message
        result = utils2.tag("v2.0.0", message="Version 2.0.0")
        assert isinstance(result, bool)
        
    def test_cli_error_paths(self, tmp_path, monkeypatch):
        """Test CLI error handling paths"""
        monkeypatch.chdir(tmp_path)
        cli = SpecPulseCLI()
        
        # Test decompose with no specs directory
        result = cli.decompose()
        assert result is False
        
        # Create specs directory but empty
        Path("specs").mkdir()
        result = cli.decompose()
        assert result is False
        
        # Test doctor on non-project
        result = cli.doctor()
        assert result is True  # Creates missing structure
        
    def test_main_cli_commands(self):
        """Test main CLI commands"""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Test init command
            result = runner.invoke(main, ['init', 'test-project'])
            assert result.exit_code == 0
            
            # Change to project
            import os
            os.chdir('test-project')
            
            # Test validate
            result = runner.invoke(main, ['validate'])
            assert result.exit_code == 0
            
            # Test sync
            result = runner.invoke(main, ['sync'])
            assert result.exit_code == 0
            
            # Test doctor
            result = runner.invoke(main, ['doctor'])
            assert result.exit_code == 0
            
            # Create a spec for decompose
            spec_dir = Path('specs') / '001-test'
            spec_dir.mkdir(parents=True)
            (spec_dir / 'spec-001.md').write_text("# Test")
            
            # Test decompose
            result = runner.invoke(main, ['decompose', '001'])
            assert result.exit_code == 0
            
            # Test decompose with flags
            result = runner.invoke(main, ['decompose', '001', '--microservices'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['decompose', '001', '--apis'])
            assert result.exit_code == 0
            
            result = runner.invoke(main, ['decompose', '001', '--interfaces'])
            assert result.exit_code == 0
            
            # Test list command
            result = runner.invoke(main, ['list'])
            assert result.exit_code == 0