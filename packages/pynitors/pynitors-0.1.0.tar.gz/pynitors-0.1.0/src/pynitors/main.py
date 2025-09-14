import psutil, time

import typer
from rich.live import Live
from rich.markdown import Markdown


app = typer.Typer()


@app.command(name="start", help="Start monitoring your system")
def pynitor(interval: float = typer.Option(1, '-i', '--interval', help="Interval in seconds")):
    """Start monitoring your system"""
    
    def get_stats():
        MARKDOWN = f"""

### Pynitor - System Monitor

* **CPU Stats**
1. **Total CPU:** {psutil.cpu_count(logical=True)}\n
2. **CPU Usage:** {psutil.cpu_percent(interval)}%\n
3. **CPU Freq:** {psutil.cpu_freq().current:.1f}Mhz\n
---------
* **Memory Stats**
1. **Total Memory:** {psutil.virtual_memory().total / (1024 **3):.2f} GB\n
2. **Available Memory:** {psutil.virtual_memory().available / (1024 **3):.2f} GB\n
3. **Used Memory:** {psutil.virtual_memory().used / (1024 **3):.2f} GB\n
4. **Memory Usage:** {psutil.virtual_memory().percent}%\n
---------
* **Disk Stats**
1. **Total Disk:** {psutil.disk_usage('/').total / (1024 **3):.2f} GB\n
2. **Used Disk:** {psutil.disk_usage('/').used / (1024 **3):.2f} GB\n
3. **Free Disk:** {psutil.disk_usage('/').free / (1024 **3):.2f} GB\n
4. **Disk Usage:** {psutil.disk_usage('/').percent}%
---------
* **Network Stats**
1. **Bytes Sent:** {psutil.net_io_counters().bytes_sent / (1024 **2):.2f} MB\n
2. **Bytes Received:** {psutil.net_io_counters().bytes_recv / (1024 **2):.2f} MB\n
3. **Packets Sent:** {psutil.net_io_counters().packets_sent}\n
4. **Packets Received:** {psutil.net_io_counters().packets_recv}\n
"""
        return Markdown(MARKDOWN)
        
    with Live(get_stats(), refresh_per_second=interval) as live:
        try:
            while True:
                live.update(get_stats())
                time.sleep(interval)
        except KeyboardInterrupt:
            typer.Exit()


