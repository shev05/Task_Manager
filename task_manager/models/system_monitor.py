# system_monitor.py

import psutil
import platform # Import platform for potentially getting CPU name differently

class SystemMonitor:
    def __init__(self):
        self.cpu_percent = 0
        self.mem_percent = 0
        self.disk_io = psutil.disk_io_counters()
        self.net_io = psutil.net_io_counters()
        self.prev_disk_io = self.disk_io
        self.prev_net_io = self.net_io
        # Добавляем хранилище для загрузки по ядрам
        self.cpu_per_core = []
        # Store initial network stats to calculate total sent/received
        self.initial_net_io = psutil.net_io_counters()


    def update_stats(self):
        self.cpu_percent = psutil.cpu_percent(percpu=False) # Общая загрузка
        self.cpu_per_core = psutil.cpu_percent(percpu=True) # Загрузка по ядрам
        self.mem_percent = psutil.virtual_memory().percent

        # Update disk and network stats
        self.prev_disk_io = self.disk_io
        self.prev_net_io = self.net_io
        self.disk_io = psutil.disk_io_counters()
        self.net_io = psutil.net_io_counters()

        # Возвращаем общую загрузку ЦП и памяти
        return self.cpu_percent, self.mem_percent

    # Добавляем новый метод для получения загрузки по ядрам
    def get_cpu_per_core(self):
        return self.cpu_per_core

    def get_cpu_info(self):
        cpu_name = platform.processor() if platform.processor() else "N/A"
        # Try to get base speed more robustly
        base_speed_ghz = "N/A"
        try:
            # On some systems, psutil.cpu_freq().max gives the max advertised frequency
            # On others, it might be the current max or dynamic.
            # Let's try to get it and format it.
            cpu_freq = psutil.cpu_freq()
            if cpu_freq and cpu_freq.max:
                 base_speed_ghz = f"{(cpu_freq.max / 1000):.2f}" # Format to 2 decimal places
        except Exception:
            pass # Keep "N/A" if it fails

        cpu_info = {
            'name': cpu_name,
            'base_speed': base_speed_ghz,
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
            'speed': "N/A" # psutil does not directly provide memory speed
        }

    def get_disk_info(self):
        disk_usage = psutil.disk_usage('/')
        # Calculate speed in MB/s
        time_delta = 1.0 # Assuming update_stats is called every second
        read_speed = (self.disk_io.read_bytes - self.prev_disk_io.read_bytes) / (1024 ** 2) / time_delta
        write_speed = (self.disk_io.write_bytes - self.prev_disk_io.write_bytes) / (1024 ** 2) / time_delta


        return {
            'usage_percent': disk_usage.percent,
            'active_time': 0, # psutil does not directly provide active time easily
            'response_time': 0, # psutil does not directly provide response time easily
            'read_speed': read_speed,
            'write_speed': write_speed
        }

    def get_network_info(self):
        # Calculate speed in Mbps
        time_delta = 1.0 # Assuming update_stats is called every second
        send_speed_bytes = (self.net_io.bytes_sent - self.prev_net_io.bytes_sent) / time_delta
        receive_speed_bytes = (self.net_io.bytes_recv - self.prev_net_io.bytes_recv) / time_delta

        send_speed_mbps = (send_speed_bytes * 8) / (1024 ** 2)
        receive_speed_mbps = (receive_speed_bytes * 8) / (1024 ** 2)

        # Calculate total sent and received in MB
        total_sent_mb = (self.net_io.bytes_sent - self.initial_net_io.bytes_sent) / (1024 ** 2)
        total_received_mb = (self.net_io.bytes_recv - self.initial_net_io.bytes_recv) / (1024 ** 2)


        return {
            'sent': total_sent_mb,
            'received': total_received_mb,
            'send_speed': send_speed_mbps,
            'receive_speed': receive_speed_mbps,
            # Network usage percent is hard to define universally without knowing link speed.
            # We can calculate a hypothetical usage based on a common speed, but it's not accurate.
            # Let's remove usage_percent or provide a placeholder.
            'usage_percent': 0 # Placeholder
        }