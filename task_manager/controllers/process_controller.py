import psutil
from typing import Tuple, List, Dict
import sys


class ProcessController:
    @staticmethod
    def get_processes() -> Tuple[List[Dict], List[Dict]]:
        """
        Получает список всех процессов и разделяет их на GUI и фоновые

        Returns:
            Tuple[List[Dict], List[Dict]]: (gui_processes, background_processes)
        """
        gui_processes = []
        background_processes = []
        current_user = ProcessController._get_current_user()

        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'username']):
            try:
                if not ProcessController._is_process_accessible(proc):
                    continue

                proc_info = ProcessController._create_process_info(proc, current_user)

                if ProcessController._is_gui_process(proc, proc_info, current_user):
                    gui_processes.append(proc_info)
                else:
                    background_processes.append(proc_info)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                print(f"Unexpected error processing PID {proc.pid if hasattr(proc, 'pid') else 'unknown'}: {e}",
                      file=sys.stderr)

        return gui_processes, background_processes

    @staticmethod
    def _get_current_user() -> str:
        """Получает имя текущего пользователя"""
        try:
            return psutil.Process().username()
        except Exception:
            return ""

    @staticmethod
    def _is_process_accessible(proc) -> bool:
        """Проверяет, доступен ли процесс для обработки"""
        try:
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except Exception:
            return False

    @staticmethod
    def _create_process_info(proc, current_user: str) -> Dict:
        """Создает словарь с информацией о процессе"""
        try:
            info = proc.info
            return {
                'pid': info.get('pid', 0),
                'name': info.get('name', 'unknown'),
                'status': info.get('status', 'unknown'),
                'cpu': info.get('cpu_percent', 0),
                'memory': info.get('memory_percent', 0),
                'user': info.get('username', 'unknown'),
                'is_current_user': info.get('username') == current_user
            }
        except Exception:
            return {
                'pid': 0,
                'name': 'unknown',
                'status': 'unknown',
                'cpu': 0,
                'memory': 0,
                'user': 'unknown',
                'is_current_user': False
            }

    @staticmethod
    def _is_gui_process(proc, proc_info: Dict, current_user: str) -> bool:
        """
        Определяет, является ли процесс GUI-приложением

        Args:
            proc: Объект процесса psutil
            proc_info: Словарь с информацией о процессе
            current_user: Имя текущего пользователя

        Returns:
            bool: True если это GUI-процесс
        """
        if not proc_info['is_current_user']:
            return False

        name = proc_info['name'].lower()
        system_keywords = [
            'systemd', 'dbus', 'pulse', 'gvfs', 'network',
            'gnome-', 'gdm', 'pipewire', 'xdg', 'ibus'
        ]

        # Исключаем системные процессы
        if any(kw in name for kw in system_keywords):
            return False

        # Исключаем процессы без интерфейса
        cli_processes = ['bash', 'sh', 'zsh', 'ssh', 'tmux', 'screen']
        if any(cli in name for cli in cli_processes):
            return False

        return True

    @staticmethod
    def terminate_process(pid: int) -> Tuple[bool, str]:
        try:
            print("ilya sluha")
            proc = psutil.Process(pid)
            proc.terminate()
            return True, f"Процесс {pid} ({proc.name()}) отправлен на завершение"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def kill_process(pid: int) -> Tuple[bool, str]:
        print("dwaawddwa")
        try:
            proc = psutil.Process(pid)
            proc.kill()
            return True, f"Процесс {pid} ({proc.name()}) принудительно завершен"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_process_details(pid: int) -> Dict:
        """
        Получает детальную информацию о процессе

        Args:
            pid: ID процесса

        Returns:
            Dict: Информация о процессе или сообщение об ошибке
        """
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                return {
                    'pid': pid,
                    'name': proc.name(),
                    'status': proc.status(),
                    'cpu_percent': proc.cpu_percent(),
                    'memory_percent': proc.memory_percent(),
                    'username': proc.username(),
                    'exe': proc.exe(),
                    'cmdline': ' '.join(proc.cmdline()),
                    'create_time': proc.create_time(),
                    'threads': proc.num_threads(),
                    'connections': len(proc.connections()),
                    'open_files': len(proc.open_files()),
                    'memory_info': proc.memory_info()._asdict()
                }
        except psutil.NoSuchProcess:
            return {'error': f'Process {pid} not found'}
        except Exception as e:
            return {'error': f'Error getting process info: {str(e)}'}