#!/usr/bin/env python3
"""
MCP Installation Helper for Claude Desktop and Claude Code
Automatically configures Claude Desktop/Code to use claude-code-indexer
"""

import json
import os
import platform
import shutil
import glob
from pathlib import Path
from typing import Dict, Any, Optional

import click
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

console = Console()


class MCPInstaller:
    """Handle MCP installation for Claude Desktop and Claude Code"""
    
    def __init__(self):
        self.platform = platform.system()
        self.desktop_config_path = self._get_desktop_config_path()
        self.code_config_path = self._get_code_config_path()
        # Default to desktop config for backward compatibility
        self.config_path = self.desktop_config_path
        self.use_claude_cli = self._check_claude_cli()
        
    def _get_desktop_config_path(self) -> Optional[Path]:
        """Get Claude Desktop config path based on platform"""
        if self.platform == "Darwin":  # macOS
            return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
        elif self.platform == "Windows":
            return Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json"
        elif self.platform == "Linux":
            return Path.home() / ".config/Claude/claude_desktop_config.json"
        else:
            return None
    
    def _get_code_config_path(self) -> Optional[Path]:
        """Get Claude Code config path based on platform"""
        if self.platform == "Darwin":  # macOS
            return Path.home() / "Library/Application Support/Claude Code/claude_desktop_config.json"
        elif self.platform == "Windows":
            return Path.home() / "AppData/Roaming/Claude Code/claude_desktop_config.json"
        elif self.platform == "Linux":
            return Path.home() / ".config/Claude Code/claude_desktop_config.json"
        else:
            return None
    
    def _check_claude_cli(self) -> bool:
        """Check if Claude CLI is available for Claude Code"""
        try:
            import subprocess
            # First check if claude command exists with --help (faster)
            result = subprocess.run(['claude', '--help'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode != 0:
                return False
            
            # Then check if mcp subcommand exists
            result = subprocess.run(['claude', 'mcp', '--help'], 
                                  capture_output=True, text=True, timeout=3)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check_claude_desktop(self) -> bool:
        """Check if Claude Desktop is installed"""
        if not self.desktop_config_path:
            return False
            
        # Check if Claude Desktop directory exists
        claude_dir = self.desktop_config_path.parent
        return claude_dir.exists()
    
    def check_claude_code(self) -> bool:
        """Check if Claude Code is installed"""
        if not self.code_config_path:
            return False
            
        # Check if Claude Code directory exists
        claude_code_dir = self.code_config_path.parent
        return claude_code_dir.exists()
    
    def detect_claude_app(self) -> str:
        """Detect which Claude app is installed"""
        # Prioritize Claude Code CLI detection
        if self.use_claude_cli:
            return "code"
        
        has_desktop = self.check_claude_desktop()
        has_code = self.check_claude_code()
        
        if has_code:
            self.config_path = self.code_config_path
            return "code"
        elif has_desktop:
            self.config_path = self.desktop_config_path
            return "desktop"
        else:
            return "none"
    
    def load_config(self) -> Dict[str, Any]:
        """Load existing Claude Desktop config"""
        if not self.config_path or not self.config_path.exists():
            return {"mcpServers": {}}
            
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"mcpServers": {}}
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save Claude Desktop config"""
        if not self.config_path:
            return False
            
        # Create directory if needed
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup existing config
        if self.config_path.exists():
            backup_path = self.config_path.with_suffix('.json.backup')
            shutil.copy2(self.config_path, backup_path)
            console.print(f"💾 Backed up existing config to: {backup_path}")
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except IOError as e:
            console.print(f"[red]❌ Failed to save config: {e}[/red]")
            return False
    
    def install(self, force: bool = False) -> bool:
        """Install MCP server configuration"""
        # Check if Claude CLI is available (Claude Code)
        if self.use_claude_cli:
            return self._install_with_claude_cli(force)
        else:
            return self._install_with_config_file(force)
    
    def _install_with_claude_cli(self, force: bool = False) -> bool:
        """Install using Claude Code CLI commands"""
        import subprocess
        
        console.print("[green]✅ Found Claude Code with CLI support[/green]")
        
        # Check if already installed
        try:
            result = subprocess.run(['claude', 'mcp', 'get', 'claude-code-indexer'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and not force:
                console.print("[yellow]⚠️  claude-code-indexer MCP server already configured[/yellow]")
                if not Confirm.ask("Update existing configuration?"):
                    return False
                
                # Remove existing first
                subprocess.run(['claude', 'mcp', 'remove', 'claude-code-indexer', '-s', 'local'], 
                             capture_output=True)
        except Exception:
            pass
        
        # Install using Claude CLI
        import sys
        try:
            # Add the MCP server using Claude Code CLI with proper command/args separation
            cmd = [
                'claude', 'mcp', 'add',
                '--scope', 'user',  # Make it available across all projects
                'claude-code-indexer',
                sys.executable,
                '--',  # Separator between command and args
                '-m', 'claude_code_indexer.mcp_server'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print("[green]✅ MCP server installed successfully with Claude Code CLI![/green]")
                console.print("• Available across all your projects")
                console.print("• Real-time code indexing and analysis")
                console.print("• No restart needed - ready to use!")
                return True
            else:
                console.print(f"[red]❌ Installation failed: {result.stderr}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Installation failed: {e}[/red]")
            return False
    
    def _install_with_config_file(self, force: bool = False) -> bool:
        """Fallback: Install using config file method for Claude Desktop"""
        # Detect which Claude app is installed
        app_type = self.detect_claude_app()
        
        if app_type == "none":
            console.print("[red]❌ Neither Claude Desktop nor Claude Code found[/red]")
            if self.desktop_config_path:
                console.print(f"Expected Claude Desktop at: {self.desktop_config_path.parent}")
            if self.code_config_path:
                console.print(f"Expected Claude Code at: {self.code_config_path.parent}")
            if not force and not Confirm.ask("Continue anyway?"):
                return False
        else:
            app_name = "Claude Code" if app_type == "code" else "Claude Desktop"
            console.print(f"[green]✅ Found {app_name}[/green]")
        
        # Load existing config
        config = self.load_config()
        
        # Check if already installed
        if "claude-code-indexer" in config.get("mcpServers", {}):
            console.print("[yellow]⚠️  claude-code-indexer MCP server already configured[/yellow]")
            if not force and not Confirm.ask("Update existing configuration?"):
                return False
        
        # Add our MCP server
        if "mcpServers" not in config:
            config["mcpServers"] = {}
            
        # Use direct MCP server for Claude Desktop
        import sys
        config["mcpServers"]["claude-code-indexer"] = {
            "command": sys.executable,
            "args": ["-m", "claude_code_indexer.mcp_server"],
            "env": {
                "PYTHONPATH": str(Path(sys.executable).parent.parent / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages")
            }
        }
        
        # Save config
        if self.save_config(config):
            app_name = "Claude Code" if app_type == "code" else "Claude Desktop"
            console.print(f"[green]✅ MCP server configured successfully for {app_name}![/green]")
            console.print(f"📁 Config location: {self.config_path}")
            console.print(f"\n[yellow]⚠️  Please restart {app_name} for changes to take effect[/yellow]")
            return True
        else:
            return False
    
    def uninstall(self) -> bool:
        """Remove MCP server configuration and perform full cleanup"""
        console.print("[bold yellow]🧹 Starting full cleanup...[/bold yellow]")
        
        # Step 1: Stop MCP daemon if running
        self._stop_mcp_daemon()
        
        # Step 2: Remove MCP configuration
        config_removed = False
        if self.use_claude_cli:
            config_removed = self._uninstall_with_claude_cli()
        else:
            config_removed = self._uninstall_with_config_file()
        
        # Step 3: Perform full cleanup regardless of config removal success
        self._full_cleanup()
        
        console.print("[bold green]✅ Full cleanup completed![/bold green]")
        return True
    
    def _uninstall_with_claude_cli(self) -> bool:
        """Uninstall using Claude Code CLI"""
        import subprocess
        
        try:
            # Try to remove from different scopes
            for scope in ['user', 'local']:
                result = subprocess.run(['claude', 'mcp', 'remove', 'claude-code-indexer', '-s', scope],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    console.print(f"[green]✅ MCP server removed from {scope} scope[/green]")
                    return True
            
            console.print("[yellow]claude-code-indexer not found in any scope[/yellow]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Uninstall failed: {e}[/red]")
            return False
    
    def _uninstall_with_config_file(self) -> bool:
        """Fallback: Uninstall using config file method"""
        # Detect which app is installed to use the right config path
        app_type = self.detect_claude_app()
        
        if not self.config_path or not self.config_path.exists():
            console.print("[yellow]No configuration found[/yellow]")
            return True
            
        config = self.load_config()
        
        if "claude-code-indexer" not in config.get("mcpServers", {}):
            console.print("[yellow]claude-code-indexer not found in config[/yellow]")
            return True
        
        # Remove our server
        del config["mcpServers"]["claude-code-indexer"]
        
        # Save config
        if self.save_config(config):
            console.print("[green]✅ MCP server removed successfully[/green]")
            return True
        else:
            return False
    
    def _stop_mcp_daemon(self) -> None:
        """Stop MCP daemon process if running"""
        import subprocess
        import psutil
        
        try:
            console.print("[cyan]🛑 Stopping MCP daemon...[/cyan]")
            
            # Try using cci command first
            try:
                result = subprocess.run(['python', '-m', 'claude_code_indexer.cli', 'mcp-daemon', 'stop'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    console.print("[green]✅ MCP daemon stopped via CLI[/green]")
                    return
            except:
                pass
            
            # Fallback: Find and kill processes by name
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if (cmdline and 
                        any('claude_code_indexer' in str(arg) for arg in cmdline) and
                        any('mcp' in str(arg).lower() for arg in cmdline)):
                        proc.kill()
                        console.print(f"[green]✅ Killed MCP process PID {proc.info['pid']}[/green]")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            console.print(f"[yellow]⚠️  Daemon cleanup: {e}[/yellow]")
    
    def _full_cleanup(self) -> None:
        """Perform comprehensive cleanup of all claude-code-indexer files"""
        import shutil
        import glob
        
        try:
            # 1. Global database cleanup
            global_db_path = Path.home() / ".claude-code-indexer"
            if global_db_path.exists():
                console.print(f"[cyan]🗑️  Removing global database ({global_db_path})...[/cyan]")
                shutil.rmtree(global_db_path)
                console.print("[green]✅ Global database removed[/green]")
            
            # 2. Get list of indexed projects before cleanup
            projects_to_clean = self._get_indexed_projects()
            
            # 3. Project-level cleanup
            console.print(f"[cyan]🗑️  Cleaning {len(projects_to_clean)} indexed projects...[/cyan]")
            for project_path in projects_to_clean:
                self._clean_project_files(project_path)
            
            # 4. Log files cleanup
            self._clean_log_files()
            
            # 5. Cache and temp files cleanup
            self._clean_cache_files()
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Cleanup warning: {e}[/yellow]")
    
    def _get_indexed_projects(self) -> list:
        """Get list of indexed projects from projects.json before it's deleted"""
        try:
            projects_json = Path.home() / ".claude-code-indexer" / "projects.json"
            if not projects_json.exists():
                return []
                
            with open(projects_json) as f:
                data = json.load(f)
            
            projects = []
            if isinstance(data, dict) and 'projects' in data:
                for project_info in data['projects'].values():
                    if isinstance(project_info, dict) and 'path' in project_info:
                        projects.append(project_info['path'])
            
            return projects
        except:
            # Fallback: return empty list, cleanup will still work for global data
            return []
    
    def _clean_project_files(self, project_path: str) -> None:
        """Clean CCI files from a specific project"""
        try:
            project_dir = Path(project_path)
            if not project_dir.exists():
                return
                
            files_removed = 0
            
            # Remove .cci_* database files
            for db_file in project_dir.glob(".cci_*.db*"):
                try:
                    db_file.unlink()
                    files_removed += 1
                except:
                    pass
            
            # Remove CLAUDE.md if it was created by CCI
            claude_md = project_dir / "CLAUDE.md"
            if claude_md.exists():
                try:
                    content = claude_md.read_text()
                    if "Claude Code Indexer" in content:
                        claude_md.unlink()
                        files_removed += 1
                except:
                    pass
            
            if files_removed > 0:
                console.print(f"[green]✅ Cleaned {files_removed} files from {project_dir.name}[/green]")
                
        except Exception as e:
            console.print(f"[yellow]⚠️  Project cleanup ({project_path}): {e}[/yellow]")
    
    def _clean_log_files(self) -> None:
        """Clean MCP log files from various locations"""
        try:
            console.print("[cyan]🗑️  Cleaning MCP log files...[/cyan]")
            log_patterns = [
                Path.home() / "Library/Application Support/Code/logs/*/window*/mcpServer.*claude-code-indexer*",
                Path.home() / "Library/Application Support/Claude/logs/*claude-code-indexer*",
                "/tmp/*claude-code-indexer*"
            ]
            
            files_removed = 0
            for pattern in log_patterns:
                try:
                    import glob
                    for log_file in glob.glob(str(pattern)):
                        try:
                            Path(log_file).unlink()
                            files_removed += 1
                        except:
                            pass
                except:
                    pass
            
            if files_removed > 0:
                console.print(f"[green]✅ Removed {files_removed} log files[/green]")
                
        except Exception as e:
            console.print(f"[yellow]⚠️  Log cleanup: {e}[/yellow]")
    
    def _clean_cache_files(self) -> None:
        """Clean cache and temporary files"""
        try:
            console.print("[cyan]🗑️  Cleaning cache files...[/cyan]")
            
            cache_dirs = [
                Path.home() / ".cache/claude-code-indexer",
                Path("/tmp") / "claude-code-indexer",
            ]
            
            dirs_removed = 0
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    try:
                        shutil.rmtree(cache_dir)
                        dirs_removed += 1
                    except:
                        pass
            
            if dirs_removed > 0:
                console.print(f"[green]✅ Cleaned {dirs_removed} cache directories[/green]")
                
        except Exception as e:
            console.print(f"[yellow]⚠️  Cache cleanup: {e}[/yellow]")
    
    def status(self) -> None:
        """Show MCP installation status"""
        table = Table(title="MCP Installation Status")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")
        
        # Platform check
        platform_supported = self.desktop_config_path is not None or self.code_config_path is not None
        table.add_row(
            "Platform",
            "✅ Supported" if platform_supported else "❌ Not Supported",
            self.platform
        )
        
        # Claude Desktop check
        desktop_installed = self.check_claude_desktop()
        table.add_row(
            "Claude Desktop",
            "✅ Found" if desktop_installed else "❌ Not Found",
            str(self.desktop_config_path.parent) if self.desktop_config_path else "N/A"
        )
        
        # Claude Code check (prioritize CLI)
        code_cli_available = self.use_claude_cli
        code_installed = self.check_claude_code()
        if code_cli_available:
            table.add_row(
                "Claude Code",
                "✅ Found (CLI)",
                "Command line tools available"
            )
        else:
            table.add_row(
                "Claude Code",
                "✅ Found" if code_installed else "❌ Not Found",
                str(self.code_config_path.parent) if self.code_config_path else "N/A"
            )
        
        # Config check
        config_exists = self.config_path and self.config_path.exists()
        table.add_row(
            "Config File",
            "✅ Exists" if config_exists else "❌ Not Found",
            str(self.config_path) if self.config_path else "N/A"
        )
        
        # MCP server check
        if config_exists:
            config = self.load_config()
            mcp_configured = "claude-code-indexer" in config.get("mcpServers", {})
            if mcp_configured:
                server_config = config["mcpServers"]["claude-code-indexer"]
                uses_daemon = "mcp_proxy" in str(server_config.get("args", []))
                mode = "Persistent Daemon" if uses_daemon else "Legacy Mode"
                table.add_row(
                    "MCP Server",
                    "✅ Configured",
                    mode
                )
            else:
                table.add_row(
                    "MCP Server",
                    "❌ Not Configured",
                    "Not installed"
                )
        else:
            table.add_row("MCP Server", "❌ Not Configured", "Config not found")
        
        # Daemon status check
        try:
            from .commands.mcp_daemon import is_daemon_running
            daemon_pid = is_daemon_running()
            if daemon_pid:
                table.add_row(
                    "MCP Daemon",
                    "✅ Running",
                    f"PID: {daemon_pid}"
                )
            else:
                table.add_row(
                    "MCP Daemon",
                    "⏸️  Not Running",
                    "Will auto-start when needed"
                )
        except:
            pass
        
        console.print(table)
        
        # Show instructions if not fully configured
        if not platform_supported:
            console.print("\n[yellow]Your platform is not supported for automatic installation.[/yellow]")
            console.print("Please manually configure Claude Desktop or Claude Code.")
        elif not desktop_installed and not code_installed:
            console.print("\n[yellow]Neither Claude Desktop nor Claude Code found. Please install one:[/yellow]")
            console.print("Claude Desktop: https://claude.ai/desktop")
            console.print("Claude Code: https://www.anthropic.com/news/claude-code")
        elif not config_exists or not mcp_configured:
            console.print("\n[cyan]To install MCP server:[/cyan]")
            console.print("claude-code-indexer mcp install")


def install_mcp(force: bool = False) -> None:
    """Install MCP server for Claude Desktop/Code"""
    installer = MCPInstaller()
    
    console.print("[bold cyan]🤖 Claude Code Indexer MCP Installer[/bold cyan]\n")
    
    # Check if MCP dependencies are installed
    try:
        import mcp
        console.print("✅ MCP SDK is installed")
    except ImportError:
        console.print("[red]❌ MCP SDK not installed[/red]")
        console.print("\nInstall with: pip install 'claude-code-indexer[mcp]'")
        return
    
    # Run installation
    if installer.install(force=force):
        console.print("\n[green]🎉 Installation complete![/green]")
        console.print("\nNext steps:")
        app_type = installer.detect_claude_app()
        app_name = "Claude Code" if app_type == "code" else "Claude Desktop"
        console.print(f"1. Restart {app_name}")
        console.print("2. Open a Python project")
        console.print("3. Claude will have access to code indexing tools automatically!")
    else:
        console.print("\n[red]Installation failed[/red]")


def uninstall_mcp() -> None:
    """Uninstall MCP server from Claude Desktop/Code with full cleanup"""
    installer = MCPInstaller()
    
    console.print("[bold cyan]🤖 Claude Code Indexer MCP Uninstaller[/bold cyan]")
    console.print("[bold yellow]⚠️  This will perform FULL CLEANUP including:[/bold yellow]")
    console.print("   • MCP configuration removal")
    console.print("   • Global database (~/.claude-code-indexer/)")
    console.print("   • Project databases (.cci_*.db)")
    console.print("   • CLAUDE.md files")
    console.print("   • Log files")
    console.print("   • Cache and daemon processes")
    console.print()
    
    app_type = installer.detect_claude_app()
    app_name = "Claude Code" if app_type == "code" else "Claude Desktop" if app_type == "desktop" else "Claude"
    
    if Confirm.ask(f"[bold red]Completely remove claude-code-indexer from {app_name} and all data?[/bold red]"):
        if installer.uninstall():
            console.print("\n[bold green]🎉 Complete removal successful![/bold green]")
            console.print("[yellow]💡 You may need to restart Claude Desktop/Code[/yellow]")
        else:
            console.print("\n[red]❌ Uninstall failed[/red]")


def show_mcp_status() -> None:
    """Show MCP installation status"""
    installer = MCPInstaller()
    installer.status()


if __name__ == "__main__":
    # Test the installer
    show_mcp_status()