# Task Scheduling & Resource Limitation System

A lightweight, modular, and extensible task scheduling and quota management framework in Python with zero external dependencies.

---

## Overview

This project provides a robust, class-based task scheduler designed to manage background jobs, enforce per-user resource limits (concurrency and execution quotas), and execute tasks asynchronously.

### Key Capabilities

- **Multi-Task Concurrency per User:** A single user can run multiple tasks simultaneously, bounded by a thread-safe `max_concurrent` quota limit.
- **Configurable Task Parameters:** Tasks support custom payloads (`params`), execution priorities, timeouts, and automatic retry policies with backoff delays.
- **Extensible Action Handlers:** Implemented using the Strategy Pattern (`BaseActionHandler` and `ActionRegistry`), allowing you to register custom actions without altering scheduler internals.
- **Thread-Safe Quota Control:** Atomically allocates and releases concurrency slots and tracks total execution budgets across worker threads.
- **Comprehensive Structured Logging:** Granular log records across all lifecycle stages (scheduler ticks, quota approvals/rejections, task dispatching, start, completion, failure, and retries).
- **Zero Dependencies:** Built entirely with the Python Standard Library (`dataclasses`, `enum`, `concurrent.futures`, `threading`, `logging`).

---

## Architecture

The system is decoupled into five distinct layers:

```
┌──────────────────────────────────────────────────────────────┐
│                       TaskScheduler                          │
│     (Evaluates due tasks, sorts by priority, loops tick)     │
└───────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                      QuotaController                         │
│   (Guards max_concurrent and max_total_executed per user)   │
└───────────────────────────────┬──────────────────────────────┘
                                │ If approved
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                        TaskExecutor                          │
│   (Dispatches tasks into ThreadPoolExecutor, manages retries)│
└───────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                    ActionRegistry & Handlers                 │
│      (SyncActionHandler, BackupActionHandler, Custom, ...)   │
└──────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
task_scheduling/
├── task_scheduling/
│   ├── __init__.py
│   ├── logger.py            # Central structured logging configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── task.py          # Task, TaskConfig, TaskStatus models
│   │   └── user.py          # User, UserQuota models
│   ├── quota/
│   │   ├── __init__.py
│   │   └── controller.py    # Thread-safe QuotaController
│   ├── executor/
│   │   ├── __init__.py
│   │   ├── base.py          # BaseActionHandler interface & ActionRegistry
│   │   ├── handlers.py      # Built-in handlers (sync, backup, delete)
│   │   └── worker_pool.py   # Asynchronous ThreadPool TaskExecutor
│   └── scheduler/
│       ├── __init__.py
│       └── engine.py        # TaskScheduler engine & tick evaluation
├── tests/
│   ├── test_logger.py
│   ├── test_models.py
│   ├── test_quota.py
│   ├── test_handlers.py
│   ├── test_executor.py
│   ├── test_scheduler.py
│   └── test_integration.py
├── scheduler.py             # Runnable demo entrypoint
├── README.md
└── .gitignore
```

---

## Quick Start

### 1. Run with Config File or Embedded Config

Run the built-in runnable demonstration in `scheduler.py`:

```bash
# Uses default config.json (or embedded dict if omitted)
python3 scheduler.py

# Or specify a custom configuration file
python3 scheduler.py my_config.json
```

---

## Configuration File (`config.json`)

You can configure users, quotas, actions, tasks, and worker limits entirely via JSON:

```json
{
  "settings": {
    "max_workers": 4,
    "log_level": "INFO"
  },
  "users": [
    {
      "id": "alice",
      "quota": {
        "max_concurrent": 2,
        "max_total_executed": 3
      }
    },
    {
      "id": "bob",
      "quota": {
        "max_concurrent": 3,
        "max_total_executed": 5
      }
    }
  ],
  "tasks": [
    {
      "user_id": "alice",
      "action": "sync",
      "params": {
        "target": "/data/x",
        "bandwidth_limit_mb": 50
      },
      "config": {
        "priority": 10,
        "timeout_seconds": 15.0,
        "max_retries": 1,
        "retry_delay_seconds": 1.0
      }
    }
  ]
}
```

You can also load directly from any Python dictionary in code:

```python
from task_scheduling.config import load_config_from_dict

app_config = load_config_from_dict(my_custom_dict)
```


---

## Usage Guide

### 1. Define Users and Quotas

```python
from task_scheduling.models.user import User, UserQuota
from task_scheduling.quota.controller import QuotaController

quota_controller = QuotaController()

# Alice can run up to 2 tasks simultaneously, and up to 10 total tasks
quota_controller.register_user(
    User(id="alice", quota=UserQuota(max_concurrent=2, max_total_executed=10))
)
```

### 2. Register Custom Action Handlers

Create a new handler by inheriting from `BaseActionHandler`:

```python
from task_scheduling.executor.base import BaseActionHandler, ActionRegistry
from task_scheduling.models.task import Task

class EmailNotificationHandler(BaseActionHandler):
    def execute(self, task: Task):
        recipient = task.params.get("to")
        subject = task.params.get("subject")
        print(f"Sending email to {recipient} with subject '{subject}'")
        return True

registry = ActionRegistry()
registry.register("send_email", EmailNotificationHandler())
```

### 3. Schedule Tasks with Configurable Parameters

```python
from datetime import datetime, timezone
from task_scheduling.models.task import Task, TaskConfig
from task_scheduling.executor.worker_pool import TaskExecutor
from task_scheduling.scheduler.engine import TaskScheduler

executor = TaskExecutor(registry, quota_controller, max_workers=4)
scheduler = TaskScheduler(quota_controller, executor)

task = Task(
    user_id="alice",
    action="send_email",
    params={"to": "user@example.com", "subject": "Daily Report"},
    scheduled_at=datetime.now(timezone.utc),
    config=TaskConfig(
        priority=10,             # Higher numbers evaluated first
        timeout_seconds=30.0,    # Task timeout
        max_retries=2,           # Automatically retried on exception
        retry_delay_seconds=2.0  # Delay between retries
    ),
)

scheduler.schedule(task)

# Trigger scheduler tick
scheduler.tick()
```

---

## Running Tests

Run the complete test suite using Python's built-in `unittest` runner:

```bash
python3 -m unittest discover -s tests -v
```

All 13 unit and integration tests cover:
- Centralized structured logging behavior
- Domain model defaults and validations
- Concurrency and total quota enforcement under concurrent access
- Extensible action handlers and registry lookup
- Thread pool asynchronous task execution and retry mechanisms
- Priority queue evaluation and quota exhaustion postponement
- End-to-end integration workflows
