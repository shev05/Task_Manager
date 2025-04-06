import psutil


class SystemMonitor:
    def __init__(self):
        self.cpu_percent = 0
        self.mem_percent = 0
        self.disk_io = psutil.disk_io_counters()
        self.net_io = psutil.net_io_counters()
        self.prev_disk_io = self.disk_io
        self.prev_net_io = self.net_io

    def update_stats(self):
        self.cpu_percent = psutil.cpu_percent()
        self.mem_percent = psutil.virtual_memory().percent

        # Update disk and network stats
        self.prev_disk_io = self.disk_io
        self.prev_net_io = self.net_io
        self.disk_io = psutil.disk_io_counters()
        self.net_io = psutil.net_io_counters()

        return self.cpu_percent, self.mem_percent

    def get_cpu_info(self):
        cpu_info = {
            'name': psutil.cpu_freq().current if psutil.cpu_freq() else "N/A",
            'base_speed': (psutil.cpu_freq().max / 1000) if psutil.cpu_freq() else "N/A",
            'cores': psutil.cpu_count(logical=False),
            'logical': psutil.cpu_count(logical=True)
        }
        return cpu_info

    def get_memory_info(self):
        mem = psutil.virtual_memory()
        return {
            'used': mem.used / (1024 ** 3),
            'total': mem.total / (1024 ** 3),
            'available': mem.available / (1024 ** 3),
            'cached': mem.cached / (1024 ** 3) if hasattr(mem, 'cached') else 0,
            'speed': "N/A"  # This information might not be available on all systems
        }

    def get_disk_info(self):
        disk_usage = psutil.disk_usage('/')
        delta = self.disk_io.read_bytes - self.prev_disk_io.read_bytes
        read_speed = delta / (1024 ** 2)  # MB/s (since update is every second)

        delta = self.disk_io.write_bytes - self.prev_disk_io.write_bytes
        write_speed = delta / (1024 ** 2)  # MB/s

        return {
            'usage_percent': disk_usage.percent,
            'active_time': 0,  # Not directly available in psutil
            'response_time': 0,  # Not directly available in psutil
            'read_speed': read_speed,
            'write_speed': write_speed
        }

    def get_network_info(self):
        delta_sent = self.net_io.bytes_sent - self.prev_net_io.bytes_sent
        delta_recv = self.net_io.bytes_recv - self.prev_net_io.bytes_recv

        return {
            'sent': self.net_io.bytes_sent / (1024 ** 2),
            'received': self.net_io.bytes_recv / (1024 ** 2),
            'send_speed': (delta_sent * 8) / (1024 ** 2),  # Mbps
            'receive_speed': (delta_recv * 8) / (1024 ** 2),  # Mbps
            'usage_percent': min(100, (delta_sent + delta_recv) / (1024 ** 2) * 0.1)  # Simple heuristic
        }