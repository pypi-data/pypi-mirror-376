from datetime import datetime
import psutil


def get_processes(user=None, limit=float("inf")):
    """
    Return a list of dictionaries. Each dictionary represents a computer process with process name, user, start time, cpu usage, and memory usage.
    If user is None, get all computer processes. Otherwise, return only processes of that user.
    """

    processes = []
    for proc in psutil.process_iter(
        ["name", "username", "create_time", "cpu_percent", "memory_info"]
    ):
        if user is None or proc.info["username"] == user:
            memory_usage = proc.info["memory_info"]
            memory_usage = None if memory_usage is None else memory_usage.rss
            process_info = {
                "pid": proc.pid,
                "name": proc.info["name"],
                "user": proc.info["username"],
                "create_time": datetime.fromtimestamp(
                    proc.info["create_time"]
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "cpu_usage": proc.info["cpu_percent"],
                "memory_usage": memory_usage,
            }
            processes.append(process_info)

            if len(processes) >= limit:
                break
    return processes


def kill_process(pid):
    """
    Terminate a process by its PID.
    """
    try:
        proc = psutil.Process(pid)
        proc.terminate()  # or proc.kill() to force kill
        return True
    except psutil.NoSuchProcess:
        return False
    except psutil.AccessDenied:
        return False
