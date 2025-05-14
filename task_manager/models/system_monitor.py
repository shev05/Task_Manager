# system_monitor.py

import psutil
import platform # Import platform for potentially getting CPU name differently

# Импортируем наш логгер
from utils.loggerService.logger import logger


class SystemMonitor:
    def __init__(self):
        logger.info("Инициализация SystemMonitor.")
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
        logger.info("SystemMonitor инициализирован.")


    def update_stats(self):
        # logger.debug("Обновление статистики системы.")
        try:
            self.cpu_percent = psutil.cpu_percent(percpu=False) # Общая загрузка
            self.cpu_per_core = psutil.cpu_percent(percpu=True) # Загрузка по ядрам
            self.mem_percent = psutil.virtual_memory().percent

            # Update disk and network stats
            self.prev_disk_io = self.disk_io
            self.prev_net_io = self.net_io
            self.disk_io = psutil.disk_io_counters()
            self.net_io = psutil.net_io_counters()

            # logger.debug("Статистика системы успешно обновлена.")
            # Возвращаем общую загрузку ЦП и памяти
            return self.cpu_percent, self.mem_percent
        except Exception as e:
            logger.error(f"Ошибка при обновлении статистики системы: {e}")
            return 0, 0 # Return default values on error

    # Добавляем новый метод для получения загрузки по ядрам
    def get_cpu_per_core(self):
        return self.cpu_per_core

    def get_cpu_info(self):
        # logger.debug("Получение информации о ЦП.")
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
                 # logger.debug(f"Определена базовая частота ЦП: {base_speed_ghz} GHz.")
            else:
                 # logger.debug("Не удалось определить базовую частоту ЦП.")
                 pass
        except Exception as e:
            logger.warning(f"Ошибка при получении частоты ЦП: {e}")
            pass # Keep "N/A" if it fails

        cpu_info = {
            'name': cpu_name,
            'base_speed': base_speed_ghz,
            'cores': psutil.cpu_count(logical=False),
            'logical': psutil.cpu_count(logical=True)
        }
        # logger.debug(f"Информация о ЦП получена: {cpu_info}")
        return cpu_info

    def get_memory_info(self):
        # logger.debug("Получение информации о памяти.")
        try:
            mem = psutil.virtual_memory()
            memory_info = {
                'used': mem.used / (1024 ** 3),
                'total': mem.total / (1024 ** 3),
                'available': mem.available / (1024 ** 3),
                'cached': mem.cached / (1024 ** 3) if hasattr(mem, 'cached') else 0,
                'speed': "N/A" # psutil does not directly provide memory speed
            }
            # logger.debug(f"Информация о памяти получена: {memory_info}")
            return memory_info
        except Exception as e:
             logger.error(f"Ошибка при получении информации о памяти: {e}")
             return {
                'used': 0, 'total': 0, 'available': 0, 'cached': 0, 'speed': "N/A"
             }


    def get_disk_info(self):
        # logger.debug("Получение информации о диске.")
        try:
            disk_usage = psutil.disk_usage('/')
            # Calculate speed in MB/s
            time_delta = 1.0 # Assuming update_stats is called every second
            read_speed = (self.disk_io.read_bytes - self.prev_disk_io.read_bytes) / (1024 ** 2) / time_delta
            write_speed = (self.disk_io.write_bytes - self.prev_disk_io.write_bytes) / (1024 ** 2) / time_delta


            disk_info = {
                'usage_percent': disk_usage.percent,
                'active_time': 0, # psutil does not directly provide active time easily
                'response_time': 0, # psutil does not directly provide response time easily
                'read_speed': read_speed,
                'write_speed': write_speed
            }
            # logger.debug(f"Информация о диске получена: {disk_info}")
            return disk_info
        except Exception as e:
            logger.error(f"Ошибка при получении информации о диске: {e}")
            return {
                 'usage_percent': 0, 'active_time': 0, 'response_time': 0, 'read_speed': 0, 'write_speed': 0
            }


    def get_network_info(self):
        # logger.debug("Получение информации о сети.")
        try:
            # Calculate speed in Mbps
            time_delta = 1.0 # Assuming update_stats is called every second
            send_speed_bytes = (self.net_io.bytes_sent - self.prev_net_io.bytes_sent) / time_delta
            receive_speed_bytes = (self.net_io.bytes_recv - self.prev_net_io.bytes_recv) / time_delta

            send_speed_mbps = (send_speed_bytes * 8) / (1024 ** 2)
            receive_speed_mbps = (receive_speed_bytes * 8) / (1024 ** 2)

            # Calculate total sent and received in MB
            total_sent_mb = (self.net_io.bytes_sent - self.initial_net_io.bytes_sent) / (1024 ** 2)
            total_received_mb = (self.net_io.bytes_recv - self.initial_net_io.bytes_recv) / (1024 ** 2)


            network_info = {
                'sent': total_sent_mb,
                'received': total_received_mb,
                'send_speed': send_speed_mbps,
                'receive_speed': receive_speed_mbps,
                # Network usage percent is hard to define universally without knowing link speed.
                # We can calculate a hypothetical usage based on a common speed, but it's not accurate.
                # Let's remove usage_percent or provide a placeholder.
                'usage_percent': 0 # Placeholder
            }
            # logger.debug(f"Информация о сети получена: {network_info}")
            return network_info
        except Exception as e:
            logger.error(f"Ошибка при получении информации о сети: {e}")
            return {
                'sent': 0, 'received': 0, 'send_speed': 0, 'receive_speed': 0, 'usage_percent': 0
            }