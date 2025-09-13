"""
Tests for the decompose functionality
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from specpulse.cli.main import SpecPulseCLI
from specpulse.core.specpulse import SpecPulse


class TestDecomposeCommand:
    """Test decompose command functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cli = SpecPulseCLI()
        self.test_project_path = Path("test_project")
        
    def test_decompose_no_specs(self, tmp_path, monkeypatch):
        """Test decompose when no specs exist"""
        monkeypatch.chdir(tmp_path)
        
        # Create empty specs directory
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        
        # Test decompose
        result = self.cli.decompose()
        assert result is False
        
    def test_decompose_with_spec_id(self, tmp_path, monkeypatch):
        """Test decompose with specific spec ID"""
        monkeypatch.chdir(tmp_path)
        
        # Create spec structure
        spec_dir = tmp_path / "specs" / "001-test-feature"
        spec_dir.mkdir(parents=True)
        
        spec_file = spec_dir / "spec-001.md"
        spec_file.write_text("# Test Specification\n\nTest content")
        
        # Test decompose
        result = self.cli.decompose(spec_id="001")
        assert result is True
        
        # Check decomposition directory created
        decomp_dir = spec_dir / "decomposition"
        assert decomp_dir.exists()
        assert (decomp_dir / "microservices.md").exists()
        assert (decomp_dir / "integration-map.md").exists()
        
    def test_decompose_microservices_only(self, tmp_path, monkeypatch):
        """Test decompose with microservices flag only"""
        monkeypatch.chdir(tmp_path)
        
        # Create spec structure
        spec_dir = tmp_path / "specs" / "001-test-feature"
        spec_dir.mkdir(parents=True)
        
        spec_file = spec_dir / "spec-001.md"
        spec_file.write_text("# Test Specification\n\nTest content")
        
        # Test decompose with microservices only
        result = self.cli.decompose(spec_id="001", microservices=True, 
                                   apis=False, interfaces=False)
        assert result is True
        
        # Check only microservices generated
        decomp_dir = spec_dir / "decomposition"
        assert (decomp_dir / "microservices.md").exists()
        assert not (decomp_dir / "api-contracts").exists()
        assert not (decomp_dir / "interfaces").exists()
        
    def test_decompose_apis_only(self, tmp_path, monkeypatch):
        """Test decompose with APIs flag only"""
        monkeypatch.chdir(tmp_path)
        
        # Create spec structure
        spec_dir = tmp_path / "specs" / "001-test-feature"
        spec_dir.mkdir(parents=True)
        
        spec_file = spec_dir / "spec-001.md"
        spec_file.write_text("# Test Specification\n\nTest content")
        
        # Test decompose with APIs only
        result = self.cli.decompose(spec_id="001", microservices=False,
                                   apis=True, interfaces=False)
        assert result is True
        
        # Check only APIs generated
        decomp_dir = spec_dir / "decomposition"
        api_dir = decomp_dir / "api-contracts"
        assert api_dir.exists()
        assert (api_dir / "auth-service.yaml").exists()
        
    def test_decompose_interfaces_only(self, tmp_path, monkeypatch):
        """Test decompose with interfaces flag only"""
        monkeypatch.chdir(tmp_path)
        
        # Create spec structure
        spec_dir = tmp_path / "specs" / "001-test-feature"
        spec_dir.mkdir(parents=True)
        
        spec_file = spec_dir / "spec-001.md"
        spec_file.write_text("# Test Specification\n\nTest content")
        
        # Test decompose with interfaces only
        result = self.cli.decompose(spec_id="001", microservices=False,
                                   apis=False, interfaces=True)
        assert result is True
        
        # Check only interfaces generated
        decomp_dir = spec_dir / "decomposition"
        iface_dir = decomp_dir / "interfaces"
        assert iface_dir.exists()
        assert (iface_dir / "IAuthService.ts").exists()
        
    def test_decompose_all_components(self, tmp_path, monkeypatch):
        """Test decompose with all components (default)"""
        monkeypatch.chdir(tmp_path)
        
        # Create spec structure
        spec_dir = tmp_path / "specs" / "001-test-feature"
        spec_dir.mkdir(parents=True)
        
        spec_file = spec_dir / "spec-001.md"
        spec_file.write_text("# Test Specification\n\nTest content")
        
        # Test decompose without flags (should generate all)
        result = self.cli.decompose(spec_id="001")
        assert result is True
        
        # Check all components generated
        decomp_dir = spec_dir / "decomposition"
        assert (decomp_dir / "microservices.md").exists()
        assert (decomp_dir / "api-contracts").exists()
        assert (decomp_dir / "interfaces").exists()
        assert (decomp_dir / "integration-map.md").exists()
        
    def test_decompose_auto_detect_spec(self, tmp_path, monkeypatch):
        """Test decompose auto-detecting most recent spec"""
        monkeypatch.chdir(tmp_path)
        
        # Create multiple specs
        spec_dir1 = tmp_path / "specs" / "001-old-feature"
        spec_dir1.mkdir(parents=True)
        spec_file1 = spec_dir1 / "spec-001.md"
        spec_file1.write_text("# Old Spec")
        
        spec_dir2 = tmp_path / "specs" / "002-new-feature"
        spec_dir2.mkdir(parents=True)
        spec_file2 = spec_dir2 / "spec-001.md"
        spec_file2.write_text("# New Spec")
        
        # Test decompose without spec_id (should use most recent)
        result = self.cli.decompose()
        assert result is True
        
        # Check decomposition in most recent spec
        decomp_dir = spec_dir2 / "decomposition"
        assert decomp_dir.exists()
        
    def test_decompose_no_spec_files(self, tmp_path, monkeypatch):
        """Test decompose when spec directory exists but no spec files"""
        monkeypatch.chdir(tmp_path)
        
        # Create spec directory without spec files
        spec_dir = tmp_path / "specs" / "001-empty-feature"
        spec_dir.mkdir(parents=True)
        
        # Test decompose
        result = self.cli.decompose(spec_id="001")
        assert result is False
        
    def test_decompose_with_hyphenated_spec_id(self, tmp_path, monkeypatch):
        """Test decompose with hyphenated spec ID like 001-feature"""
        monkeypatch.chdir(tmp_path)
        
        # Create spec structure
        spec_dir = tmp_path / "specs" / "001-test-feature"
        spec_dir.mkdir(parents=True)
        
        spec_file = spec_dir / "spec-001.md"
        spec_file.write_text("# Test Specification\n\nTest content")
        
        # Test decompose with full hyphenated ID
        result = self.cli.decompose(spec_id="001-test-feature")
        assert result is True
        
        # Check decomposition created
        decomp_dir = spec_dir / "decomposition"
        assert decomp_dir.exists()


class TestDecomposeTemplates:
    """Test decomposition template functionality"""
    
    def test_get_decomposition_template_microservices(self):
        """Test getting microservices template"""
        sp = SpecPulse()
        template = sp.get_decomposition_template("microservices")
        assert "{{ feature_name }}" in template
        assert "{{ services }}" in template
        
    def test_get_decomposition_template_api(self):
        """Test getting API contract template"""
        sp = SpecPulse()
        template = sp.get_decomposition_template("api")
        assert "{{ service_name }}" in template
        assert "{{ paths }}" in template
        
    def test_get_decomposition_template_interface(self):
        """Test getting interface template"""
        sp = SpecPulse()
        template = sp.get_decomposition_template("interface")
        assert "{{ interface_name }}" in template
        assert "{{ methods }}" in template
        
    def test_get_decomposition_template_fallback(self):
        """Test template fallback for non-existent template"""
        sp = SpecPulse()
        
        # Mock the template path to not exist
        with patch.object(Path, 'exists', return_value=False):
            template = sp.get_decomposition_template("microservices")
            # Should return fallback template
            assert "{{ feature_name }}" in template
            assert "{{ services }}" in template
            
    def test_get_decomposition_template_unknown_type(self):
        """Test getting unknown template type"""
        sp = SpecPulse()
        
        # Mock the template path to not exist
        with patch.object(Path, 'exists', return_value=False):
            template = sp.get_decomposition_template("unknown")
            # Should return empty string for unknown types
            assert template == ""


class TestDecomposeScripts:
    """Test decomposition scripts"""
    
    def test_decompose_python_script(self, tmp_path, monkeypatch):
        """Test sp-pulse-decompose.py script"""
        monkeypatch.chdir(tmp_path)
        
        # Create spec structure
        spec_dir = tmp_path / "specs" / "001-test"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec-001.md"
        spec_file.write_text("# Test")
        
        # Import and run the script
        import subprocess
        import sys
        
        # Get the script path
        script_path = Path(__file__).parent.parent / "specpulse" / "resources" / "scripts" / "sp-pulse-decompose.py"
        
        if script_path.exists():
            result = subprocess.run(
                [sys.executable, str(script_path), "001"],
                capture_output=True,
                text=True,
                cwd=tmp_path
            )
            
            # Check script output - script now outputs different format
            assert "[SpecPulse Decompose]" in result.stdout
            assert "SPEC_FILE" in result.stdout