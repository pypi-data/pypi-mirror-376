#!/usr/bin/env python3
"""
Test suite for SpecPulse PowerShell scripts
Tests the functionality of pulse-init.ps1, pulse-spec.ps1, pulse-plan.ps1, and pulse-task.ps1
"""

import unittest
from pathlib import Path
import tempfile
import shutil
import os
import sys
import subprocess
import platform


class TestSpecPulsePowerShellScripts(unittest.TestCase):
    """Test SpecPulse PowerShell script functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create mock project structure
        self.project_root = Path(self.temp_dir) / "specpulse"
        self.project_root.mkdir()
        (self.project_root / "resources" / "templates").mkdir(parents=True)
        (self.project_root / "memory").mkdir()
        
        # Create mock templates
        templates = {
            "spec.md": """# Specification: {{ feature_name }}

## Metadata
- Feature ID: {{ feature_id }}
- Created: {{ creation_date }}
- Status: Draft

## Overview
{{ feature_description }}

## Requirements

### Functional Requirements
- [ ] Requirement 1
- [ ] Requirement 2

### Technical Requirements
- [ ] Technical requirement 1
- [ ] Technical requirement 2

## Acceptance Criteria
- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2

## Notes
[NEEDS CLARIFICATION: Add more specific requirements]
""",
            "plan.md": """# Implementation Plan: {{ feature_name }}

## Metadata
- Feature ID: {{ feature_id }}
- Created: {{ creation_date }}
- Status: Draft

## Technology Stack
- Language: Python
- Framework: Flask
- Database: SQLite

## Architecture Overview
{{ architecture_overview }}

## Implementation Phases

### Phase 1: Foundation
- [ ] Set up project structure
- [ ] Configure development environment

### Phase 2: Core Features
- [ ] Implement core functionality
- [ ] Create API endpoints

### Phase 3: Polish
- [ ] Add error handling
- [ ] Write documentation

## Testing Strategy
- Unit tests for core functionality
- Integration tests for API endpoints
- End-to-end tests for user workflows

## Notes
[NEEDS CLARIFICATION: Define specific technical stack]
""",
            "task.md": """# Task List: {{ feature_name }}

## Metadata
- Feature ID: {{ feature_id }}
- Created: {{ creation_date }}
- Status: Draft

## Task Breakdown

### Critical Path (Phase 0)
- [ ] T001: [S] Set up development environment
- [ ] T002: [S] Create project structure

### Phase 1: Foundation
- [ ] T003: [M] Implement core modules
- [ ] T004: [M] Set up database schema

### Phase 2: Core Features
- [ ] T005: [L] Implement user authentication
- [ ] T006: [L] Create API endpoints

### Phase 3: Polish
- [ ] T007: [S] Add error handling
- [ ] T008: [S] Write documentation

## Progress Tracking
Total tasks: 8
Completed: 0
Remaining: 8

## Notes
[NEEDS CLARIFICATION: Estimate task durations]
"""
        }
        
        for template_name, content in templates.items():
            template_file = self.project_root / "resources" / "templates" / template_name
            template_file.write_text(content)
        
        # Copy scripts to test directory
        self.copy_scripts_to_test_dir()
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def copy_scripts_to_test_dir(self):
        """Copy scripts to test directory for testing"""
        original_scripts_dir = Path(__file__).parent.parent / "specpulse" / "resources" / "scripts"
        test_scripts_dir = self.project_root / "resources" / "scripts"
        test_scripts_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all PowerShell script files
        for script_file in original_scripts_dir.glob("*.ps1"):
            shutil.copy2(script_file, test_scripts_dir)
    
    def is_windows(self):
        """Check if running on Windows"""
        return platform.system().lower() == "windows"
    
    def run_powershell_script(self, script_path, args=None, cwd=None):
        """Run a PowerShell script and return the result"""
        if not self.is_windows():
            self.skipTest("PowerShell scripts can only be tested on Windows")
        
        if args is None:
            args = []
        
        # Build PowerShell command
        ps_command = f"& '{script_path}'"
        for arg in args:
            ps_command += f" '{arg}'"
        
        # Execute PowerShell command
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd or self.project_root
        )
        
        return result
    
    def test_pulse_init_script_functionality(self):
        """Test pulse-init.ps1 script functionality"""
        scripts_dir = self.project_root / "resources" / "scripts"
        init_script = scripts_dir / "pulse-init.ps1"
        
        if not init_script.exists():
            self.skipTest("pulse-init.ps1 not found")
        
        if not self.is_windows():
            self.skipTest("PowerShell scripts can only be tested on Windows")
        
        # Test script execution with a valid feature name
        result = self.run_powershell_script(init_script, ["test-feature"])
        
        # Should succeed
        self.assertEqual(result.returncode, 0, 
                        f"pulse-init.ps1 failed: {result.stderr}")
        
        # Check that feature directories were created
        feature_dirs = [
            self.project_root / "specs" / "001-test-feature",
            self.project_root / "plans" / "001-test-feature",
            self.project_root / "tasks" / "001-test-feature"
        ]
        
        for feature_dir in feature_dirs:
            self.assertTrue(feature_dir.exists(), f"Feature directory {feature_dir} not created")
        
        # Check that templates were copied
        template_files = [
            feature_dirs[0] / "spec.md",
            feature_dirs[1] / "plan.md",
            feature_dirs[2] / "tasks.md"
        ]
        
        for template_file in template_files:
            self.assertTrue(template_file.exists(), f"Template file {template_file} not copied")
    
    def test_pulse_spec_script_functionality(self):
        """Test pulse-spec.ps1 script functionality"""
        scripts_dir = self.project_root / "resources" / "scripts"
        init_script = scripts_dir / "pulse-init.ps1"
        spec_script = scripts_dir / "pulse-spec.ps1"
        
        if not spec_script.exists():
            self.skipTest("pulse-spec.ps1 not found")
        
        if not self.is_windows():
            self.skipTest("PowerShell scripts can only be tested on Windows")
        
        # First create a feature using pulse-init.ps1
        init_result = self.run_powershell_script(init_script, ["test-feature"])
        
        self.assertEqual(init_result.returncode, 0, 
                        f"pulse-init.ps1 failed: {init_result.stderr}")
        
        # Extract the feature directory name from the init output
        feature_dir_name = None
        for line in init_result.stdout.split('\n'):
            if line.startswith('BRANCH_NAME='):
                feature_dir_name = line.split('=')[1]
                break
        
        self.assertIsNotNone(feature_dir_name, "Could not extract feature directory name")
        
        # Test script execution with the feature directory
        result = self.run_powershell_script(spec_script, [feature_dir_name, "user authentication system"])
        
        # Should succeed
        self.assertEqual(result.returncode, 0, 
                        f"pulse-spec.ps1 failed: {result.stderr}")
        
        # Check that spec file was created
        spec_file = self.project_root / "specs" / feature_dir_name / "spec.md"
        self.assertTrue(spec_file.exists(), "Specification file not created")
        
        # Check that content was populated
        content = spec_file.read_text()
        self.assertIn("user authentication system", content)
    
    def test_pulse_plan_script_functionality(self):
        """Test pulse-plan.ps1 script functionality"""
        scripts_dir = self.project_root / "resources" / "scripts"
        init_script = scripts_dir / "pulse-init.ps1"
        plan_script = scripts_dir / "pulse-plan.ps1"
        
        if not plan_script.exists():
            self.skipTest("pulse-plan.ps1 not found")
        
        if not self.is_windows():
            self.skipTest("PowerShell scripts can only be tested on Windows")
        
        # First create a feature using pulse-init.ps1
        init_result = self.run_powershell_script(init_script, ["test-feature"])
        
        self.assertEqual(init_result.returncode, 0, 
                        f"pulse-init.ps1 failed: {init_result.stderr}")
        
        # Extract the feature directory name from the init output
        feature_dir_name = None
        for line in init_result.stdout.split('\n'):
            if line.startswith('BRANCH_NAME='):
                feature_dir_name = line.split('=')[1]
                break
        
        self.assertIsNotNone(feature_dir_name, "Could not extract feature directory name")
        
        # Create a spec file for reference
        spec_file = self.project_root / "specs" / feature_dir_name / "spec.md"
        spec_file.write_text("# Specification: test-feature\n\n## Requirements\n- User authentication\n- Session management\n")
        
        # Test script execution
        result = self.run_powershell_script(plan_script, [feature_dir_name])
        
        # Should succeed
        self.assertEqual(result.returncode, 0, 
                        f"pulse-plan.ps1 failed: {result.stderr}")
        
        # Check that plan file was created
        plan_file = self.project_root / "plans" / feature_dir_name / "plan.md"
        self.assertTrue(plan_file.exists(), "Plan file not created")
        
        # Check that content was populated
        content = plan_file.read_text()
        self.assertIn("Technology Stack", content)
    
    def test_pulse_task_script_functionality(self):
        """Test pulse-task.ps1 script functionality"""
        scripts_dir = self.project_root / "resources" / "scripts"
        init_script = scripts_dir / "pulse-init.ps1"
        task_script = scripts_dir / "pulse-task.ps1"
        
        if not task_script.exists():
            self.skipTest("pulse-task.ps1 not found")
        
        if not self.is_windows():
            self.skipTest("PowerShell scripts can only be tested on Windows")
        
        # First create a feature using pulse-init.ps1
        init_result = self.run_powershell_script(init_script, ["test-feature"])
        
        self.assertEqual(init_result.returncode, 0, 
                        f"pulse-init.ps1 failed: {init_result.stderr}")
        
        # Extract the feature directory name from the init output
        feature_dir_name = None
        for line in init_result.stdout.split('\n'):
            if line.startswith('BRANCH_NAME='):
                feature_dir_name = line.split('=')[1]
                break
        
        self.assertIsNotNone(feature_dir_name, "Could not extract feature directory name")
        
        # Create a plan file for reference
        plan_file = self.project_root / "plans" / feature_dir_name / "plan.md"
        plan_file.write_text("# Implementation Plan: test-feature\n\n## Technology Stack\n- Python\n- Flask\n\n## Implementation Phases\n### Phase 1: Foundation\n- Set up project structure\n- Configure database\n")
        
        # Test script execution
        result = self.run_powershell_script(task_script, [feature_dir_name])
        
        # Should succeed
        self.assertEqual(result.returncode, 0, 
                        f"pulse-task.ps1 failed: {result.stderr}")
        
        # Check that task file was created
        task_file = self.project_root / "tasks" / feature_dir_name / "tasks.md"
        self.assertTrue(task_file.exists(), "Task file not created")
        
        # Check that content was populated
        content = task_file.read_text()
        self.assertIn("Task Breakdown", content)
    
    def test_powershell_script_error_handling(self):
        """Test PowerShell script error handling"""
        scripts_dir = self.project_root / "resources" / "scripts"
        init_script = scripts_dir / "pulse-init.ps1"
        
        if not init_script.exists():
            self.skipTest("pulse-init.ps1 not found")
        
        if not self.is_windows():
            self.skipTest("PowerShell scripts can only be tested on Windows")
        
        # Test with invalid feature name (should fail)
        result = self.run_powershell_script(init_script, [""])  # Empty feature name
        
        # Should fail with error
        self.assertNotEqual(result.returncode, 0, 
                           "pulse-init.ps1 should fail with empty feature name")
        self.assertIn("ERROR", result.stderr.upper(), 
                      "Error message should contain ERROR")
    
    def test_powershell_script_unicode_handling(self):
        """Test PowerShell script Unicode handling"""
        scripts_dir = self.project_root / "resources" / "scripts"
        init_script = scripts_dir / "pulse-init.ps1"
        
        if not init_script.exists():
            self.skipTest("pulse-init.ps1 not found")
        
        if not self.is_windows():
            self.skipTest("PowerShell scripts can only be tested on Windows")
        
        # Test with Unicode feature name
        unicode_name = "test-feature-unicode-≤≥→←"
        result = self.run_powershell_script(init_script, [unicode_name])
        
        # Should handle Unicode properly
        self.assertEqual(result.returncode, 0, 
                        f"pulse-init.ps1 failed with Unicode: {result.stderr}")
        
        # Check that feature directory was created with sanitized name
        feature_dir = self.project_root / "specs" / "001-test-feature-unicode"
        self.assertTrue(feature_dir.exists(), "Unicode feature directory not created")
    
    def test_powershell_script_file_permissions(self):
        """Test PowerShell script file permissions"""
        scripts_dir = self.project_root / "resources" / "scripts"
        init_script = scripts_dir / "pulse-init.ps1"
        
        if not init_script.exists():
            self.skipTest("pulse-init.ps1 not found")
        
        if not self.is_windows():
            self.skipTest("PowerShell scripts can only be tested on Windows")
        
        # Test file creation and permissions
        result = self.run_powershell_script(init_script, ["permissions-test"])
        
        # Should succeed
        self.assertEqual(result.returncode, 0, 
                        f"pulse-init.ps1 failed: {result.stderr}")
        
        # Check that created files are readable
        spec_file = self.project_root / "specs" / "001-permissions-test" / "spec.md"
        if spec_file.exists():
            self.assertTrue(os.access(spec_file, os.R_OK), "Spec file is not readable")
    
    def test_powershell_script_logging(self):
        """Test PowerShell script logging"""
        scripts_dir = self.project_root / "resources" / "scripts"
        init_script = scripts_dir / "pulse-init.ps1"
        
        if not init_script.exists():
            self.skipTest("pulse-init.ps1 not found")
        
        if not self.is_windows():
            self.skipTest("PowerShell scripts can only be tested on Windows")
        
        # Test logging output
        result = self.run_powershell_script(init_script, ["logging-test"])
        
        # Should succeed
        self.assertEqual(result.returncode, 0, 
                        f"pulse-init.ps1 failed: {result.stderr}")
        
        # Check that logging output contains expected information
        self.assertIn("initializing feature", result.stderr.lower(), 
                      "Logging should contain initialization message")
    
    def test_powershell_script_syntax_validation(self):
        """Test PowerShell script syntax validation"""
        scripts_dir = self.project_root / "resources" / "scripts"
        
        if not self.is_windows():
            self.skipTest("PowerShell scripts can only be tested on Windows")
        
        # Test that all PowerShell scripts have valid syntax
        ps_scripts = list(scripts_dir.glob("*.ps1"))
        
        for script in ps_scripts:
            # Test syntax by running PowerShell syntax check
            result = subprocess.run([
                "powershell", "-Command", f"Get-Command -Syntax '{script}'"
            ], capture_output=True, text=True, timeout=30)
            
            self.assertEqual(result.returncode, 0, 
                           f"PowerShell script {script.name} has syntax errors: {result.stderr}")


if __name__ == '__main__':
    unittest.main()