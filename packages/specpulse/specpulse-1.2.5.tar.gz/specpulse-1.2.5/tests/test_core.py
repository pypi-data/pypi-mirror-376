"""
Tests for the core.specpulse module
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from specpulse.core.specpulse import SpecPulse


class TestSpecPulse:
    """Test SpecPulse core functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.sp = SpecPulse()
        
    def test_init(self):
        """Test SpecPulse initialization"""
        sp = SpecPulse()
        assert sp.project_root is None
        assert sp.config == {}
        
    def test_init_with_project_root(self):
        """Test SpecPulse initialization with project root"""
        sp = SpecPulse(project_root=Path("/test/path"))
        assert sp.project_root == Path("/test/path")
        
    def test_find_project_root_current_dir(self, tmp_path, monkeypatch):
        """Test finding project root in current directory"""
        monkeypatch.chdir(tmp_path)
        
        # Create constitution file
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "constitution.md").touch()
        
        root = self.sp.find_project_root()
        assert root == tmp_path
        
    def test_find_project_root_parent_dir(self, tmp_path, monkeypatch):
        """Test finding project root in parent directory"""
        # Create project structure
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "constitution.md").touch()
        
        # Create subdirectory and change to it
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        monkeypatch.chdir(subdir)
        
        root = self.sp.find_project_root()
        assert root == tmp_path
        
    def test_find_project_root_not_found(self, tmp_path, monkeypatch):
        """Test when project root is not found"""
        monkeypatch.chdir(tmp_path)
        
        root = self.sp.find_project_root()
        assert root is None
        
    def test_load_config_success(self, tmp_path):
        """Test loading configuration successfully"""
        # Create config file
        config_file = tmp_path / ".specpulse.yaml"
        config_file.write_text("""
project_name: test-project
version: 1.0.0
settings:
  ai_provider: claude
        """)
        
        sp = SpecPulse(project_root=tmp_path)
        config = sp.load_config()
        
        assert config["project_name"] == "test-project"
        assert config["version"] == "1.0.0"
        assert config["settings"]["ai_provider"] == "claude"
        
    def test_load_config_no_file(self, tmp_path):
        """Test loading config when file doesn't exist"""
        sp = SpecPulse(project_root=tmp_path)
        config = sp.load_config()
        
        assert config == {}
        
    def test_save_config(self, tmp_path):
        """Test saving configuration"""
        sp = SpecPulse(project_root=tmp_path)
        config = {
            "project_name": "test-project",
            "version": "1.0.0"
        }
        
        result = sp.save_config(config)
        assert result is True
        
        # Verify file was created
        config_file = tmp_path / ".specpulse.yaml"
        assert config_file.exists()
        
    def test_get_template_spec(self):
        """Test getting specification template"""
        template = self.sp.get_template("spec")
        
        assert "# {{ feature_name }} Specification" in template
        assert "[NEEDS CLARIFICATION]" in template
        
    def test_get_template_plan(self):
        """Test getting plan template"""
        template = self.sp.get_template("plan")
        
        assert "# {{ feature_name }} Implementation Plan" in template
        assert "## Phase" in template
        
    def test_get_template_task(self):
        """Test getting task template"""
        template = self.sp.get_template("task")
        
        assert "# {{ feature_name }} Task Breakdown" in template
        assert "T[" in template
        
    def test_get_template_constitution(self):
        """Test getting constitution template"""
        template = self.sp.get_template("constitution")
        
        assert "# Project Constitution" in template
        assert "## Core Principles" in template
        
    def test_get_template_context(self):
        """Test getting context template"""
        template = self.sp.get_template("context")
        
        assert "# Project Context" in template
        assert "## Current Feature" in template
        
    def test_get_template_decisions(self):
        """Test getting decisions template"""
        template = self.sp.get_template("decisions")
        
        assert "# Architecture Decisions" in template
        
    def test_get_template_invalid(self):
        """Test getting invalid template returns empty string"""
        template = self.sp.get_template("invalid")
        
        assert template == ""
        
    def test_get_template_with_file_exists(self, tmp_path):
        """Test getting template when file exists"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create custom template
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "spec.md").write_text("Custom spec template")
        
        template = sp.get_template("spec")
        assert template == "Custom spec template"
        
    def test_get_decomposition_template_microservices(self):
        """Test getting microservices decomposition template"""
        template = self.sp.get_decomposition_template("microservices")
        
        assert "{{ feature_name }}" in template
        assert "{{ services }}" in template
        
    def test_get_decomposition_template_api(self):
        """Test getting API decomposition template"""
        template = self.sp.get_decomposition_template("api")
        
        assert "{{ service_name }}" in template
        assert "{{ paths }}" in template
        
    def test_get_decomposition_template_interface(self):
        """Test getting interface decomposition template"""
        template = self.sp.get_decomposition_template("interface")
        
        assert "{{ interface_name }}" in template
        assert "{{ methods }}" in template
        
    def test_get_decomposition_template_integration(self):
        """Test getting integration plan template"""
        template = self.sp.get_decomposition_template("integration")
        
        assert "{{ feature_name }}" in template
        assert "Integration Plan" in template
        
    def test_get_decomposition_template_service_plan(self):
        """Test getting service plan template"""
        template = self.sp.get_decomposition_template("service_plan")
        
        assert "{{ service_name }}" in template
        assert "Service Plan" in template
        
    def test_get_decomposition_template_invalid(self):
        """Test getting invalid decomposition template"""
        template = self.sp.get_decomposition_template("invalid")
        
        assert template == ""
        
    def test_get_decomposition_template_with_file(self, tmp_path):
        """Test getting decomposition template when file exists"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create custom template
        templates_dir = tmp_path / "templates" / "decomposition"
        templates_dir.mkdir(parents=True)
        (templates_dir / "microservices.md").write_text("Custom microservices template")
        
        template = sp.get_decomposition_template("microservices")
        assert template == "Custom microservices template"
        
    def test_create_project_structure(self, tmp_path):
        """Test creating project structure"""
        sp = SpecPulse(project_root=tmp_path)
        
        result = sp.create_project_structure()
        assert result is True
        
        # Check directories
        assert (tmp_path / "specs").exists()
        assert (tmp_path / "plans").exists()
        assert (tmp_path / "tasks").exists()
        assert (tmp_path / "memory").exists()
        assert (tmp_path / "templates").exists()
        assert (tmp_path / "scripts").exists()
        assert (tmp_path / ".claude").exists()
        assert (tmp_path / ".gemini").exists()
        
    def test_validate_structure_valid(self, tmp_path):
        """Test validating valid project structure"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create all required directories
        for dir_name in ["specs", "plans", "tasks", "memory", "templates", "scripts"]:
            (tmp_path / dir_name).mkdir()
            
        # Create constitution
        (tmp_path / "memory" / "constitution.md").write_text("# Constitution")
        
        result = sp.validate_structure()
        assert result is True
        
    def test_validate_structure_missing_dirs(self, tmp_path):
        """Test validating structure with missing directories"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create only some directories
        (tmp_path / "specs").mkdir()
        (tmp_path / "memory").mkdir()
        
        result = sp.validate_structure()
        assert result is False
        
    def test_validate_structure_missing_constitution(self, tmp_path):
        """Test validating structure with missing constitution"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create all directories but no constitution
        for dir_name in ["specs", "plans", "tasks", "memory", "templates", "scripts"]:
            (tmp_path / dir_name).mkdir()
            
        result = sp.validate_structure()
        assert result is False
        
    def test_sync_templates(self, tmp_path):
        """Test syncing templates"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create templates directory
        (tmp_path / "templates").mkdir()
        
        result = sp.sync_templates()
        assert result is True
        
        # Check templates were created
        assert (tmp_path / "templates" / "spec.md").exists()
        assert (tmp_path / "templates" / "plan.md").exists()
        assert (tmp_path / "templates" / "task.md").exists()
        
    def test_get_latest_spec_none(self, tmp_path):
        """Test getting latest spec when none exist"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create specs directory
        (tmp_path / "specs").mkdir()
        
        spec = sp.get_latest_spec()
        assert spec is None
        
    def test_get_latest_spec_single(self, tmp_path):
        """Test getting latest spec with single spec"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create spec
        specs_dir = tmp_path / "specs"
        spec_dir = specs_dir / "001-test"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec-001.md"
        spec_file.write_text("# Test Spec")
        
        spec = sp.get_latest_spec()
        assert spec == spec_file
        
    def test_get_latest_spec_multiple(self, tmp_path):
        """Test getting latest spec with multiple specs"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create multiple specs
        specs_dir = tmp_path / "specs"
        for i in range(1, 4):
            spec_dir = specs_dir / f"00{i}-test{i}"
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "spec-001.md"
            spec_file.write_text(f"# Test Spec {i}")
            
        spec = sp.get_latest_spec()
        assert spec.parent.name == "003-test3"
        
    def test_get_spec_by_id_full(self, tmp_path):
        """Test getting spec by full ID"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create spec
        specs_dir = tmp_path / "specs"
        spec_dir = specs_dir / "001-test-feature"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec-001.md"
        spec_file.write_text("# Test Spec")
        
        spec = sp.get_spec_by_id("001-test-feature")
        assert spec == spec_file
        
    def test_get_spec_by_id_numeric(self, tmp_path):
        """Test getting spec by numeric ID"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create spec
        specs_dir = tmp_path / "specs"
        spec_dir = specs_dir / "001-test-feature"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec-001.md"
        spec_file.write_text("# Test Spec")
        
        spec = sp.get_spec_by_id("001")
        assert spec == spec_file
        
    def test_get_spec_by_id_not_found(self, tmp_path):
        """Test getting spec by ID when not found"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create specs directory
        (tmp_path / "specs").mkdir()
        
        spec = sp.get_spec_by_id("999")
        assert spec is None
        
    def test_list_all_specs_empty(self, tmp_path):
        """Test listing specs when empty"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create specs directory
        (tmp_path / "specs").mkdir()
        
        specs = sp.list_all_specs()
        assert specs == []
        
    def test_list_all_specs_multiple(self, tmp_path):
        """Test listing multiple specs"""
        sp = SpecPulse(project_root=tmp_path)
        
        # Create multiple specs
        specs_dir = tmp_path / "specs"
        for i in range(1, 4):
            spec_dir = specs_dir / f"00{i}-test{i}"
            spec_dir.mkdir(parents=True)
            spec_file = spec_dir / "spec-001.md"
            spec_file.write_text(f"# Test Spec {i}")
            
        specs = sp.list_all_specs()
        assert len(specs) == 3
        assert all(spec.suffix == ".md" for spec in specs)