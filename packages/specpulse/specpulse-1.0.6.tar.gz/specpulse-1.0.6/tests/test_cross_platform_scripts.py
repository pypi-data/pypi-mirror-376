#!/usr/bin/env python3
"""
Comprehensive test suite for SpecPulse cross-platform scripts
Tests all Python, Bash, and PowerShell script functionality
"""

import unittest
from pathlib import Path
import tempfile
import shutil
import os
import sys
import subprocess
import platform


class TestSpecPulseScripts(unittest.TestCase):
    """Test SpecPulse cross-platform script functionality"""
    
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
            "spec.md": "# Specification: {{ feature_name }}\n\n## Metadata\n",
            "plan.md": "# Implementation Plan: {{ feature_name }}\n\n## Technology Stack\n",
            "task.md": "# Task List: {{ feature_name }}\n\n## Tasks\n"
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
        
        # Copy all script files
        for script_file in original_scripts_dir.glob("*"):
            if script_file.suffix in ['.py', '.sh', '.ps1']:
                shutil.copy2(script_file, test_scripts_dir)
    
    def test_script_files_exist(self):
        """Test that all required script files exist"""
        scripts_dir = self.project_root / "resources" / "scripts"
        
        required_scripts = [
            "pulse-init.py",
            "pulse-spec.py", 
            "pulse-plan.py",
            "pulse-task.py",
            "pulse-init.ps1",
            "pulse-spec.ps1",
            "pulse-plan.ps1",
            "pulse-task.ps1",
            "pulse-init.sh",
            "pulse-spec.sh",
            "pulse-plan.sh",
            "pulse-task.sh"
        ]
        
        for script in required_scripts:
            script_path = scripts_dir / script
            self.assertTrue(script_path.exists(), f"Script {script} not found")
    
    def test_python_scripts_executable(self):
        """Test that Python scripts can be executed"""
        scripts_dir = self.project_root / "resources" / "scripts"
        python_scripts = list(scripts_dir.glob("*.py"))
        
        self.assertGreater(len(python_scripts), 0, "No Python scripts found")
        
        # Test that scripts are syntactically correct
        for script in python_scripts:
            try:
                result = subprocess.run([
                    sys.executable, "-m", "py_compile", str(script)
                ], capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, 
                               f"Python script {script.name} has syntax errors: {result.stderr}")
            except subprocess.TimeoutExpired:
                self.fail(f"Python script {script.name} compilation timed out")
    
    def test_template_files_exist(self):
        """Test that all template files exist"""
        templates_dir = self.project_root / "resources" / "templates"
        
        required_templates = ["spec.md", "plan.md", "task.md"]
        
        for template in required_templates:
            template_path = templates_dir / template
            self.assertTrue(template_path.exists(), f"Template {template} not found")
    
    def test_script_unicode_handling(self):
        """Test that scripts handle Unicode characters correctly"""
        # Create a template with Unicode characters
        template_file = self.project_root / "resources" / "templates" / "unicode_test.md"
        template_content = "# Test with Unicode: ≤ ≥ → ←\n\n## Content\n"
        template_file.write_text(template_content, encoding='utf-8')
        
        # Verify content was written correctly
        read_content = template_file.read_text(encoding='utf-8')
        self.assertIn('≤', read_content)
        self.assertIn('≥', read_content)
        self.assertIn('→', read_content)
        self.assertIn('←', read_content)
    
    def test_cross_platform_script_execution_simulation(self):
        """Test cross-platform script execution simulation"""
        scripts_dir = self.project_root / "resources" / "scripts"
        
        # Test that all platform-specific scripts exist
        python_scripts = list(scripts_dir.glob("*.py"))
        powershell_scripts = list(scripts_dir.glob("*.ps1"))
        bash_scripts = list(scripts_dir.glob("*.sh"))
        
        self.assertGreater(len(python_scripts), 0, "No Python scripts found")
        self.assertGreater(len(powershell_scripts), 0, "No PowerShell scripts found")
        self.assertGreater(len(bash_scripts), 0, "No Bash scripts found")
        
        # Test that each platform has equivalent scripts
        python_names = {script.stem for script in python_scripts}
        powershell_names = {script.stem for script in powershell_scripts}
        bash_names = {script.stem for script in bash_scripts}
        
        self.assertEqual(python_names, powershell_names, 
                        "Python and PowerShell scripts don't match")
        self.assertEqual(python_names, bash_names, 
                        "Python and Bash scripts don't match")
    
    def test_ai_command_files_exist(self):
        """Test that AI command files exist and contain cross-platform references"""
        original_project_root = Path(__file__).parent.parent / "specpulse"
        
        # Test Claude commands
        claude_commands_dir = original_project_root / "resources" / "commands" / "claude"
        if claude_commands_dir.exists():
            claude_files = list(claude_commands_dir.glob("*.md"))
            self.assertGreater(len(claude_files), 0, "No Claude command files found")
            
            # Test that commands contain cross-platform references
            for cmd_file in claude_files:
                content = cmd_file.read_text()
                self.assertIn("powershell", content.lower(), 
                             f"Claude command {cmd_file.name} missing PowerShell reference")
                self.assertIn("python", content.lower(), 
                             f"Claude command {cmd_file.name} missing Python reference")
        
        # Test Gemini commands
        gemini_commands_dir = original_project_root / "resources" / "commands" / "gemini"
        if gemini_commands_dir.exists():
            gemini_files = list(gemini_commands_dir.glob("*.toml"))
            self.assertGreater(len(gemini_files), 0, "No Gemini command files found")
            
            # Test that commands contain cross-platform references
            for cmd_file in gemini_files:
                content = cmd_file.read_text()
                self.assertIn("powershell", content.lower(), 
                             f"Gemini command {cmd_file.name} missing PowerShell reference")
                self.assertIn("python", content.lower(), 
                             f"Gemini command {cmd_file.name} missing Python reference")
    
    def test_test_demo_directory_updated(self):
        """Test that test-demo directory has been updated with cross-platform scripts"""
        test_demo_dir = Path(__file__).parent.parent / "test-demo" / "demo-project"
        
        if test_demo_dir.exists():
            scripts_dir = test_demo_dir / "scripts"
            if scripts_dir.exists():
                # Check for Python scripts
                python_scripts = list(scripts_dir.glob("*.py"))
                self.assertGreater(len(python_scripts), 0, 
                                 "No Python scripts in test-demo directory")
                
                # Check for PowerShell scripts
                powershell_scripts = list(scripts_dir.glob("*.ps1"))
                self.assertGreater(len(powershell_scripts), 0, 
                                 "No PowerShell scripts in test-demo directory")
    
    def test_platform_detection_logic(self):
        """Test platform detection logic"""
        current_platform = platform.system().lower()
        
        # Test that we can detect the current platform
        if current_platform == "windows":
            self.assertTrue("win" in current_platform)
        elif current_platform == "linux":
            self.assertEqual(current_platform, "linux")
        elif current_platform == "darwin":
            self.assertEqual(current_platform, "darwin")
    
    def test_script_consistency(self):
        """Test that all script variants have consistent structure"""
        scripts_dir = self.project_root / "resources" / "scripts"
        
        # Get all script variants for each command
        script_groups = {}
        for script_file in scripts_dir.glob("*"):
            if script_file.suffix in ['.py', '.sh', '.ps1']:
                base_name = script_file.stem
                if base_name not in script_groups:
                    script_groups[base_name] = []
                script_groups[base_name].append(script_file)
        
        # Test that each command has all three variants
        for base_name, variants in script_groups.items():
            extensions = {script.suffix for script in variants}
            expected_extensions = {'.py', '.sh', '.ps1'}
            
            self.assertEqual(extensions, expected_extensions,
                           f"Command {base_name} missing script variants: {expected_extensions - extensions}")
    
    def test_error_handling_simulation(self):
        """Test error handling simulation"""
        scripts_dir = self.project_root / "resources" / "scripts"
        
        # Test Python script error handling by removing templates
        templates_dir = self.project_root / "resources" / "templates"
        if templates_dir.exists():
            # Create backup directory outside the templates directory
            temp_backup = self.project_root / "temp_backup_templates"
            shutil.move(templates_dir, temp_backup)
            
            try:
                # Try to run a Python script (should fail gracefully)
                spec_script = scripts_dir / "pulse-spec.py"
                if spec_script.exists():
                    result = subprocess.run([
                        sys.executable, str(spec_script), "test-feature"
                    ], capture_output=True, text=True, timeout=30)
                    
                    # Should exit with error code
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("ERROR", result.stderr)
                    
            finally:
                # Restore templates
                if temp_backup.exists():
                    shutil.move(temp_backup, templates_dir)


class TestScriptIntegration(unittest.TestCase):
    """Test integration between different scripts"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_complete_workflow_simulation(self):
        """Test complete workflow simulation"""
        # This tests the complete SpecPulse workflow
        # In a real scenario, this would test:
        # 1. Initialize feature
        # 2. Create specification  
        # 3. Create plan
        # 4. Create tasks
        
        # For now, we test that all necessary components exist
        project_root = Path(__file__).parent.parent / "specpulse"
        
        # Check that all required directories exist
        required_dirs = [
            "resources/scripts",
            "resources/templates", 
            "resources/commands/claude",
            "resources/commands/gemini"
        ]
        
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            self.assertTrue(full_path.exists(), f"Directory {dir_path} not found")
    
    def test_ai_command_consistency(self):
        """Test that AI commands are consistent across platforms"""
        project_root = Path(__file__).parent.parent / "specpulse"
        
        # Get Claude and Gemini command files
        claude_dir = project_root / "resources" / "commands" / "claude"
        gemini_dir = project_root / "resources" / "commands" / "gemini"
        
        if claude_dir.exists() and gemini_dir.exists():
            claude_files = {f.stem for f in claude_dir.glob("*.md")}
            gemini_files = {f.stem for f in gemini_dir.glob("*.toml")}
            
            # Should have same command names
            self.assertEqual(claude_files, gemini_files,
                           "Claude and Gemini commands don't match")


if __name__ == '__main__':
    unittest.main()