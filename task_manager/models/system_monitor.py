import psutil


class SystemMonitor:
    def __init__(self):
        self.cpu_percent = 0
        self.mem_percent = 0

    def update_stats(self):
        self.cpu_percent = psutil.cpu_percent()
        self.mem_percent = psutil.virtual_memory().percent
        return self.cpu_percent, self.mem_percent