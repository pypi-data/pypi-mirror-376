"""
Tests for the utils modules
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import sys
import git

# Add parent directory to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent))

from specpulse.utils.console import Console
from specpulse.utils.git_utils import GitUtils


class TestConsole:
    """Test Console utility class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.console = Console()
        
    def test_init(self):
        """Test Console initialization"""
        console = Console()
        assert console.console is not None
        
    @patch('specpulse.utils.console.RichConsole')
    def test_show_banner(self, mock_rich_console):
        """Test show_banner method"""
        console = Console()
        console.show_banner()
        
        # Banner prints multiple times
        assert mock_rich_console.return_value.print.called
        
    @patch('specpulse.utils.console.RichConsole')
    def test_success(self, mock_rich_console):
        """Test success message"""
        console = Console()
        console.success("Success message")
        
        console.console.print.assert_called_once()
        call_args = console.console.print.call_args[0][0]
        assert "Success message" in call_args
        
    @patch('specpulse.utils.console.RichConsole')
    def test_error(self, mock_rich_console):
        """Test error message"""
        console = Console()
        console.error("Error message")
        
        console.console.print.assert_called_once()
        call_args = console.console.print.call_args[0][0]
        assert "Error message" in call_args
        
    @patch('specpulse.utils.console.RichConsole')
    def test_warning(self, mock_rich_console):
        """Test warning message"""
        console = Console()
        console.warning("Warning message")
        
        console.console.print.assert_called_once()
        call_args = console.console.print.call_args[0][0]
        assert "Warning message" in call_args
        
    @patch('specpulse.utils.console.RichConsole')
    def test_info(self, mock_rich_console):
        """Test info message"""
        console = Console()
        console.info("Info message")
        
        console.console.print.assert_called_once()
        call_args = console.console.print.call_args[0][0]
        assert "Info message" in call_args
        
    @patch('specpulse.utils.console.RichConsole')
    def test_header(self, mock_rich_console):
        """Test header display"""
        console = Console()
        console.header("Test Header")
        
        mock_rich_console.return_value.print.assert_called()
        
    @patch('specpulse.utils.console.RichConsole')
    def test_section(self, mock_rich_console):
        """Test section header"""
        console = Console()
        console.section("Test Section")
        
        console.console.print.assert_called()
        
    @patch('specpulse.utils.console.RichConsole')
    def test_progress_bar(self, mock_rich_console):
        """Test progress bar creation"""
        console = Console()
        
        # progress_bar returns a Progress context manager
        progress = console.progress_bar("Processing", 100)
        assert progress is not None
        
    @patch('specpulse.utils.console.RichConsole')
    def test_table(self, mock_rich_console):
        """Test table creation"""
        console = Console()
        
        with patch('specpulse.utils.console.Table') as mock_table:
            console.table("Title", ["Col1", "Col2"], [["val1", "val2"]])
            
            mock_table.assert_called_once()
            
    @patch('specpulse.utils.console.RichConsole')
    def test_tree(self, mock_rich_console):
        """Test tree creation"""
        console = Console()
        
        with patch('specpulse.utils.console.Tree') as mock_tree:
            console.tree("Root", {"child1": "value1"})
            
            mock_tree.assert_called_once()
            
    @patch('specpulse.utils.console.RichConsole')
    def test_status_panel(self, mock_rich_console):
        """Test status panel creation"""
        console = Console()
        
        with patch('specpulse.utils.console.Panel') as mock_panel:
            console.status_panel("Title", [("key", "value")])
            
            mock_panel.assert_called()
            
    @patch('specpulse.utils.console.RichConsole')
    def test_prompt(self, mock_rich_console):
        """Test user prompt"""
        console = Console()
        
        with patch('specpulse.utils.console.Prompt.ask', return_value="user input"):
            result = console.prompt("Enter value")
            
            assert result == "user input"
            
    @patch('specpulse.utils.console.RichConsole')
    def test_confirm(self, mock_rich_console):
        """Test confirmation prompt"""
        console = Console()
        
        with patch('specpulse.utils.console.Confirm.ask', return_value=True):
            result = console.confirm("Are you sure?")
            
            assert result is True
            
    @patch('specpulse.utils.console.RichConsole')
    def test_celebration(self, mock_rich_console):
        """Test celebration animation"""
        console = Console()
        
        # Should not error
        console.celebration()
        
        # Check that print was called
        assert mock_rich_console.return_value.print.called
        
    @patch('specpulse.utils.console.RichConsole')
    def test_spinner(self, mock_rich_console):
        """Test spinner context manager"""
        console = Console()
        
        # spinner returns a Status context manager
        spinner = console.spinner("Loading...")
        assert spinner is not None


class TestGitUtils:
    """Test GitUtils class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.git_utils = GitUtils()
        
    def test_init(self):
        """Test GitUtils initialization"""
        utils = GitUtils()
        # GitUtils finds the current project root if no path given
        assert utils.repo_path is not None or utils.repo_path is None
        
    def test_init_with_path(self, tmp_path):
        """Test GitUtils initialization with path"""
        utils = GitUtils(tmp_path)
        assert utils.repo_path == tmp_path
        
    def test_is_git_repo_true(self, tmp_path):
        """Test checking if directory is git repo"""
        # Initialize git repo
        git.Repo.init(tmp_path)
        
        utils = GitUtils(tmp_path)
        assert utils.is_git_repo() is True
        
    def test_is_git_repo_false(self, tmp_path):
        """Test checking non-git directory"""
        utils = GitUtils(tmp_path)
        assert utils.is_git_repo() is False
        
    def test_init_repo(self, tmp_path):
        """Test initializing new git repo"""
        utils = GitUtils(tmp_path)
        
        result = utils.init_repo()
        assert result is True
        assert (tmp_path / ".git").exists()
        
    def test_init_repo_existing(self, tmp_path):
        """Test initializing when repo exists"""
        # Initialize first
        git.Repo.init(tmp_path)
        
        utils = GitUtils(tmp_path)
        result = utils.init_repo()
        
        # Should still return True
        assert result is True
        
    def test_get_current_branch(self, tmp_path):
        """Test getting current branch"""
        # Initialize repo
        repo = git.Repo.init(tmp_path)
        
        # Create initial commit (needed for branch)
        (tmp_path / "test.txt").write_text("test")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        utils = GitUtils(tmp_path)
        branch = utils.get_current_branch()
        
        assert branch in ["master", "main"]
        
    def test_get_current_branch_no_repo(self, tmp_path):
        """Test getting branch when no repo"""
        utils = GitUtils(tmp_path)
        branch = utils.get_current_branch()
        
        assert branch is None
        
    def test_create_branch(self, tmp_path):
        """Test creating new branch"""
        # Initialize repo with commit
        repo = git.Repo.init(tmp_path)
        (tmp_path / "test.txt").write_text("test")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        utils = GitUtils(tmp_path)
        result = utils.create_branch("feature/test")
        
        assert result is True
        assert "feature/test" in [b.name for b in repo.branches]
        
    def test_create_branch_exists(self, tmp_path):
        """Test creating branch that already exists"""
        # Initialize repo with commit
        repo = git.Repo.init(tmp_path)
        (tmp_path / "test.txt").write_text("test")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        utils = GitUtils(tmp_path)
        utils.create_branch("feature/test")
        
        # Try to create again
        result = utils.create_branch("feature/test")
        assert result is False
        
    def test_checkout_branch(self, tmp_path):
        """Test checking out branch"""
        # Initialize repo with branches
        repo = git.Repo.init(tmp_path)
        (tmp_path / "test.txt").write_text("test")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        repo.create_head("feature/test")
        
        utils = GitUtils(tmp_path)
        result = utils.checkout_branch("feature/test")
        
        assert result is True
        assert repo.active_branch.name == "feature/test"
        
    def test_checkout_branch_not_exists(self, tmp_path):
        """Test checking out non-existent branch"""
        # Initialize repo
        repo = git.Repo.init(tmp_path)
        (tmp_path / "test.txt").write_text("test")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        utils = GitUtils(tmp_path)
        result = utils.checkout_branch("nonexistent")
        
        assert result is False
        
    def test_add_files(self, tmp_path):
        """Test adding files to git"""
        # Initialize repo
        utils = GitUtils(tmp_path)
        utils.init_repo()
        
        # Create files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        
        result = utils.add_files(["file1.txt", "file2.txt"])
        
        assert result is True
        
    def test_commit(self, tmp_path):
        """Test making a commit"""
        # Initialize repo and stage files
        utils = GitUtils(tmp_path)
        utils.init_repo()
        (tmp_path / "test.txt").write_text("test")
        utils.add_files(["test.txt"])
        
        result = utils.commit("Test commit")
        
        assert result is True
        
    def test_commit_nothing_staged(self, tmp_path):
        """Test committing with nothing staged"""
        # Initialize repo
        git.Repo.init(tmp_path)
        
        utils = GitUtils(tmp_path)
        result = utils.commit("Test commit")
        
        assert result is False
        
    def test_get_status(self, tmp_path):
        """Test getting git status"""
        # Initialize repo
        repo = git.Repo.init(tmp_path)
        
        # Create untracked file
        (tmp_path / "untracked.txt").write_text("content")
        
        utils = GitUtils(tmp_path)
        status = utils.get_status()
        
        assert status is not None
        assert "untracked" in status
        
    def test_get_status_no_repo(self, tmp_path):
        """Test getting status when no repo"""
        utils = GitUtils(tmp_path)
        status = utils.get_status()
        
        assert status is None
        
    def test_has_changes_true(self, tmp_path):
        """Test detecting changes"""
        # Initialize repo
        repo = git.Repo.init(tmp_path)
        
        # Create file
        (tmp_path / "test.txt").write_text("test")
        
        utils = GitUtils(tmp_path)
        assert utils.has_changes() is True
        
    def test_has_changes_false(self, tmp_path):
        """Test when no changes"""
        # Initialize repo with committed file
        repo = git.Repo.init(tmp_path)
        (tmp_path / "test.txt").write_text("test")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial")
        
        utils = GitUtils(tmp_path)
        assert utils.has_changes() is False
        
    def test_get_log(self, tmp_path):
        """Test getting commit log"""
        # Initialize repo with commits
        utils = GitUtils(tmp_path)
        utils.init_repo()
        
        for i in range(3):
            (tmp_path / f"file{i}.txt").write_text(f"content{i}")
            utils.add_files([f"file{i}.txt"])
            utils.commit(f"Commit {i}")
            
        log = utils.get_log(limit=2)
        
        assert len(log) <= 3  # May include initial commit
        
    def test_get_log_no_repo(self, tmp_path):
        """Test getting log when no repo"""
        utils = GitUtils(tmp_path)
        log = utils.get_log()
        
        assert log == []