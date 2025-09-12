"""
Background Daemon Commands
Control the revolutionary terminal job notification system
"""

import click
import time
from rich.console import Console
from rich.panel import Panel
from pathlib import Path

from ..core.display import console, show_error, show_success
from ..core.notification_daemon import start_daemon, stop_daemon, daemon_status, check_notifications_once

@click.group()
def daemon():
    """🤖 Control background job notification daemon"""
    pass

@daemon.command()
@click.option('--foreground', is_flag=True, help='Run in foreground (for debugging)')
def start(foreground):
    """Start the job notification daemon"""
    
    console.print(Panel.fit(
        """
[bold bright_yellow]🚀 STARTING REVOLUTIONARY FEATURE![/bold bright_yellow]

[cyan]The Jobtty notification daemon will:[/cyan]
• Monitor your saved searches continuously
• Send job alerts directly to your terminal
• Show notifications while you're coding
• Work across all terminal sessions

[green]This is the world's first terminal-native job notification system![/green]
        """,
        title="[bold white]🤖 Notification Daemon[/bold white]", 
        border_style="bright_yellow"
    ))
    
    try:
        start_daemon(background=not foreground)
        
        if foreground:
            console.print("🔄 Running in foreground mode...")
            console.print("Press Ctrl+C to stop")
        else:
            console.print("✅ Daemon started in background")
            console.print("💡 Use [bold]jobtty daemon status[/bold] to check status")
            
    except Exception as e:
        show_error(f"Failed to start daemon: {str(e)}")

@daemon.command()
def stop():
    """Stop the job notification daemon"""
    
    console.print("🛑 Stopping notification daemon...")
    
    try:
        stop_daemon()
        show_success("Daemon stopped successfully")
    except Exception as e:
        show_error(f"Failed to stop daemon: {str(e)}")

@daemon.command()
def status():
    """Check daemon status and recent activity"""
    
    console.print(Panel.fit(
        "[bold cyan]🤖 JOBTTY NOTIFICATION DAEMON STATUS[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        daemon_status()
    except Exception as e:
        show_error(f"Failed to check status: {str(e)}")

@daemon.command()
def restart():
    """Restart the notification daemon"""
    
    console.print("🔄 Restarting notification daemon...")
    
    try:
        stop_daemon()
        time.sleep(1)
        start_daemon()
        show_success("Daemon restarted successfully")
    except Exception as e:
        show_error(f"Failed to restart daemon: {str(e)}")

@daemon.command()
def test():
    """Test notification system manually"""
    
    console.print("🧪 Testing notification system...")
    console.print("🔍 Checking all saved searches for new jobs...")
    
    try:
        check_notifications_once()
        show_success("Test completed - check for any notifications!")
    except Exception as e:
        show_error(f"Test failed: {str(e)}")

@daemon.command()
def logs():
    """Show daemon logs"""
    
    from pathlib import Path
    log_file = Path.home() / ".jobtty" / "daemon.log"
    
    if not log_file.exists():
        console.print("📄 No daemon logs found")
        return
    
    console.print("[bold cyan]📋 Recent Daemon Logs:[/bold cyan]\n")
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        # Show last 20 lines
        for line in lines[-20:]:
            console.print(line.strip())
            
    except Exception as e:
        show_error(f"Failed to read logs: {str(e)}")

@daemon.command()
@click.option('--background', '-b', is_flag=True, help='Run in background')
def listen(background):
    """🔊 Listen for terminal job notifications"""
    
    from pathlib import Path
    import subprocess
    
    console.print(Panel.fit(
        """
[bold bright_green]🔊 LISTENING FOR JOB NOTIFICATIONS![/bold bright_green]

[cyan]This terminal will now receive:[/cyan]
• Real-time job alerts from your saved searches
• Direct notifications while coding
• Quick apply/dismiss options

[yellow]Keep this terminal open to receive notifications![/yellow]
        """,
        title="[bold white]🔔 Notification Listener[/bold white]", 
        border_style="bright_green"
    ))
    
    pipe_dir = Path.home() / ".jobtty" / "pipes"
    pipe_dir.mkdir(exist_ok=True)
    notification_pipe = pipe_dir / "notifications"
    
    try:
        # Create named pipe if it doesn't exist
        if not notification_pipe.exists():
            import os
            os.mkfifo(str(notification_pipe))
        
        console.print(f"📡 Listening on: {notification_pipe}")
        console.print("🔄 Press Ctrl+C to stop listening\n")
        
        # Listen for notifications
        if background:
            # Background mode - just setup the pipe
            console.print("✅ Background listener setup complete")
            console.print("💡 Notifications will appear in this terminal")
        else:
            # Foreground mode - actively listen
            import select
            import os
            
            while True:
                try:
                    # Open pipe for reading (blocking)
                    with open(notification_pipe, 'r') as pipe:
                        notification = pipe.read().strip()
                        if notification:
                            # Clear screen and show notification
                            console.clear()
                            console.print(notification)
                            console.print("\n[dim]Press Enter to continue...[/dim]")
                            input()
                except KeyboardInterrupt:
                    console.print("\n🔴 Stopped listening for notifications")
                    break
                except Exception as e:
                    console.print(f"⚠️  Listener error: {e}")
                    time.sleep(1)
                    
    except Exception as e:
        show_error(f"Failed to setup notification listener: {str(e)}")

# Register with CLI
if __name__ == "__main__":
    daemon()