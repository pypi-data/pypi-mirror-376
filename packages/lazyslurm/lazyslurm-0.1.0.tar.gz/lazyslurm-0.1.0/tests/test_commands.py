import pytest
import psutil
from lazyslurm.process.commands import get_processes


class MockProcess:
    def __init__(self, name, username, pid, create_time, cpu_percent, memory_info):
        self.info = {
            "name": name,
            "username": username,
            "create_time": create_time,
            "cpu_percent": cpu_percent,
            "memory_info": memory_info,
        }
        self.pid = pid

    @staticmethod
    def process_iter(attrs):
        return [
            MockProcess(
                "python",
                "user1",
                10,
                1633072000,
                0.5,
                type("mem", (object,), {"rss": 2048}),
            ),
            MockProcess(
                "bash",
                "user2",
                11,
                1633072060,
                0.1,
                type("mem", (object,), {"rss": 1024}),
            ),
        ]


# Monkey patching psutil.process_iter

psutil.process_iter = MockProcess.process_iter


def test_get_processes():
    # Test with no user filter
    processes = get_processes()
    assert len(processes) == 2
    assert processes[0]["name"] == "python"
    assert processes[1]["name"] == "bash"

    # Test with user filter
    user1_processes = get_processes(user="user1")
    assert len(user1_processes) == 1
    # Removing unnecessary indentation
    assert user1_processes[0]["name"] == "python"


# Monkey patching psutil.process_iter
import psutil

psutil.process_iter = MockProcess.process_iter


def test_get_processes():
    # Test with no user filter
    processes = get_processes()
    assert len(processes) == 2
    assert processes[0]["name"] == "python"
    assert processes[1]["name"] == "bash"

    # Test with user filter
    user1_processes = get_processes(user="user1")
    assert len(user1_processes) == 1
    assert user1_processes[0]["name"] == "python"
