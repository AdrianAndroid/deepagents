#!/usr/bin/env python3
"""Comprehensive coding capability benchmark for Volcengine (huoshan) models.

Tests 11 models across 7 dimensions of large-project coding ability:
  1. Algorithm implementation
  2. System design / architecture
  3. Debugging / bug fixing
  4. Refactoring
  5. Code comprehension / explanation
  6. Multi-file project generation
  7. Edge case handling / robustness

Each model x each test case = 1 evaluation. Results are scored automatically
where possible (syntax check, test execution) and by heuristics otherwise.

Usage:
    OPENAI_API_KEY=... uv run --project libs/code python libs/code/scripts/benchmark_huoshan_models.py

Output:
    libs/code/scripts/benchmark_results_<timestamp>.json
    libs/code/scripts/benchmark_report_<timestamp>.md
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass, field, asdict
from pathlib import Path

from langchain_openai import ChatOpenAI

# -- Configuration ------------------------------------------------------

BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"
API_KEY = os.environ.get("OPENAI_API_KEY", "")
TIMEOUT = 300  # 5 min per call

MODELS = [
    "doubao-seed-2.0-code",
    "doubao-seed-2.0-pro",
    "doubao-seed-2.0-lite",
    "doubao-seed-2.0-mini",
    "glm-5.2",
    "kimi-k2.7-code",
    "deepseek-v4-pro",
    "deepseek-v4-flash",
    "minimax-m3",
    "minimax-m2.7",
    "kimi-k2.6",
]

# -- Test Cases ---------------------------------------------------------


@dataclass
class TestCase:
    """A single benchmark test case."""

    id: str
    name: str
    dimension: str
    prompt: str
    expected_keywords: list[str] = field(default_factory=list)
    language: str = "python"
    max_tokens: int = 8192
    runnable: bool = True
    test_input: str | None = None
    expected_output_pattern: str | None = None


TEST_CASES: list[TestCase] = [
    # 1. Algorithm Implementation
    TestCase(
        id="algo_lru_cache",
        name="LRU Cache Implementation",
        dimension="algorithm",
        prompt="""Implement an LRU (Least Recently Used) cache in Python with the following requirements:
1. O(1) get and put operations
2. Thread-safe (use threading.Lock)
3. Generic type support (TypeVar)
4. Eviction callback support (optional)
5. Capacity property
6. Clear and __len__ methods
7. Full type hints and docstrings

Provide a complete, production-ready implementation.""",
        expected_keywords=["class", "Lock", "TypeVar", "capacity", "def get", "def put"],
        max_tokens=8192,
    ),
    TestCase(
        id="algo_graph_dijkstra",
        name="Dijkstra with Priority Queue",
        dimension="algorithm",
        prompt="""Implement Dijkstra's shortest path algorithm in Python with:
1. Using heapq for priority queue
2. Support for both directed and undirected graphs
3. Return both distances and paths
4. Handle disconnected nodes (return float('inf'))
5. Early termination when target is found
6. Type hints throughout
7. A Graph class with add_edge method

Write comprehensive code.""",
        expected_keywords=["heapq", "class Graph", "def dijkstra", "float", "def add_edge"],
        max_tokens=8192,
    ),
    TestCase(
        id="algo_concurrent_rate_limiter",
        name="Token Bucket Rate Limiter (async)",
        dimension="algorithm",
        prompt="""Implement an async token bucket rate limiter in Python with:
1. AsyncIO compatible (async/await)
2. Configurable rate (tokens per second) and burst capacity
3. acquire(timeout) method that waits if no tokens available
4. Thread-safe for concurrent async tasks
5. Statistics: total_requests, total_throttled, current_tokens
6. Context manager support (async with)
7. Full type hints and docstrings

Production-ready code only.""",
        expected_keywords=["async", "asyncio", "Lock", "class", "acquire", "tokens", "capacity"],
        max_tokens=8192,
    ),
    # 2. System Design / Architecture
    TestCase(
        id="design_event_system",
        name="Event-Driven Architecture Design",
        dimension="system_design",
        prompt="""Design and implement a complete event-driven pub/sub system in Python with:
1. Event base class with timestamp, event_id, event_type
2. EventPublisher with subscribe/unsubscribe/publish methods
3. Support for filtered subscriptions (subscribe to specific event types)
4. Async event handlers
5. Error handling (one handler failure doesn't block others)
6. Event replay capability (store events, replay from timestamp)
7. Dead letter queue for failed events
8. Metrics (total events, per-handler success/failure counts)

Write ALL classes with full type hints. Make it production quality.""",
        expected_keywords=["class Event", "class EventPublisher", "subscribe", "publish", "async", "DeadLetter", "replay", "metrics"],
        max_tokens=12288,
    ),
    TestCase(
        id="design_plugin_architecture",
        name="Plugin Architecture with Hot Reload",
        dimension="system_design",
        prompt="""Design a plugin architecture system in Python that supports:
1. Plugin base class with lifecycle hooks: on_load, on_unload, on_enable, on_disable
2. PluginManager that discovers plugins from a directory
3. Hot-reload: reload a plugin at runtime without restarting
4. Dependency declaration between plugins (plugin A requires plugin B)
5. Plugin isolation (one plugin crash doesn't bring down the system)
6. Plugin configuration via TOML
7. Version compatibility checking
8. Event bus for inter-plugin communication

Provide complete implementation with all classes.""",
        expected_keywords=["class Plugin", "PluginManager", "on_load", "on_unload", "reload", "depend", "EventBus", "version"],
        max_tokens=12288,
    ),
    # 3. Debugging / Bug Fixing
    TestCase(
        id="debug_race_condition",
        name="Fix Race Condition in Bank Transfer",
        dimension="debugging",
        prompt="""The following code has race conditions and bugs. Fix ALL issues and explain each fix.

```python
import threading

class BankAccount:
    def __init__(self, balance=0):
        self.balance = balance

    def transfer(self, other, amount):
        if self.balance >= amount:
            self.balance -= amount
            other.balance += amount
            return True
        return False

class Bank:
    def __init__(self):
        self.accounts = {}

    def create_account(self, name, balance=0):
        self.accounts[name] = BankAccount(balance)

    def transfer(self, from_name, to_name, amount):
        return self.accounts[from_name].transfer(self.accounts[to_name], amount)

    def total_balance(self):
        return sum(a.balance for a in self.accounts.values())
```

Issues to fix:
1. Race condition on concurrent transfers
2. Deadlock potential
3. No error handling for missing accounts
4. No audit trail
5. Transfer atomicity

Provide the complete fixed code with explanations.""",
        expected_keywords=["Lock", "RLock", "try", "except", "raise", "audit", "atomic", "with"],
        max_tokens=8192,
    ),
    TestCase(
        id="debug_memory_leak",
        name="Fix Memory Leak in Event Handler",
        dimension="debugging",
        prompt="""The following code has memory leaks and design issues. Fix ALL bugs and explain.

```python
class EventManager:
    def __init__(self):
        self.handlers = []
        self.events = []

    def subscribe(self, handler):
        self.handlers.append(handler)

    def emit(self, event):
        self.events.append(event)
        for handler in self.handlers:
            handler(event)

    def get_history(self):
        return self.events

    def unsubscribe(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)

class DataProcessor:
    def __init__(self, manager):
        self.manager = manager
        self.manager.subscribe(self.handle)
        self.cache = {}

    def handle(self, event):
        self.cache[event.id] = event.data

    def cleanup(self):
        pass  # TODO
```

Issues:
1. Memory leak: events list grows unbounded
2. Memory leak: cache grows unbounded
3. Memory leak: unsubscribe doesn't work with bound methods
4. No weak references for handlers
5. cleanup() is empty

Provide complete fixed code.""",
        expected_keywords=["weakref", "deque", "maxlen", "WeakSet", "cleanup"],
        max_tokens=8192,
    ),
    # 4. Refactoring
    TestCase(
        id="refactor_god_class",
        name="Refactor God Class into SRP Modules",
        dimension="refactoring",
        prompt="""Refactor the following God Class into proper SRP (Single Responsibility) modules.
Split into separate classes, add type hints, error handling, and tests.

```python
class UserManager:
    def __init__(self):
        self.users = []
        self.db_conn = None
        self.email_queue = []
        self.audit_log = []

    def create_user(self, name, email, role):
        user = {'id': len(self.users)+1, 'name': name, 'email': email, 'role': role, 'active': True}
        self.users.append(user)
        self.db_conn.execute(f"INSERT INTO users VALUES ({user['id']}, '{name}', '{email}', '{role}')")
        self.email_queue.append({'to': email, 'subject': 'Welcome', 'body': f'Hi {name}'})
        self.audit_log.append(f"User {name} created with role {role}")
        return user

    def delete_user(self, user_id):
        for u in self.users:
            if u['id'] == user_id:
                u['active'] = False
                self.db_conn.execute(f"UPDATE users SET active=0 WHERE id={user_id}")
                self.email_queue.append({'to': u['email'], 'subject': 'Account Deleted', 'body': 'Your account has been deleted'})
                self.audit_log.append(f"User {u['name']} deleted")
                return True
        return False

    def send_emails(self):
        for email in self.email_queue:
            print(f"Sending to {email['to']}: {email['subject']}")
        self.email_queue.clear()

    def get_audit_log(self):
        return self.audit_log

    def validate_email(self, email):
        return '@' in email

    def validate_role(self, role):
        return role in ['admin', 'user', 'guest']
```

Provide:
1. All refactored classes (UserRepository, EmailService, AuditService, UserValidator, UserService)
2. Proper type hints
3. Error handling with custom exceptions
4. A UserService facade that coordinates them
5. Integration test code""",
        expected_keywords=["class UserRepository", "class EmailService", "class AuditService", "class UserValidator", "class UserService", "Exception", "def test"],
        max_tokens=12288,
    ),
    # 5. Code Comprehension
    TestCase(
        id="comprehend_async_decorator",
        name="Explain Complex Async Decorator",
        dimension="comprehension",
        prompt="""Read the following code and provide:
1. A detailed explanation of what it does
2. Line-by-line analysis of the tricky parts
3. Potential issues or bugs
4. Three suggested improvements

```python
import asyncio
import functools
import time
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
):
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        await asyncio.sleep(delay)
                    else:
                        raise
            raise last_exc

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        time.sleep(delay)
                    else:
                        raise
            raise last_exc

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
```

Provide a thorough analysis.""",
        expected_keywords=["retry", "backoff", "exponential", "async", "ParamSpec", "TypeVar", "decorator"],
        runnable=False,
        max_tokens=8192,
    ),
    # 6. Multi-file Project Generation
    TestCase(
        id="project_rest_api",
        name="Complete REST API Project with SQLite",
        dimension="project_generation",
        prompt="""Create a complete REST API project for a task management system. Include ALL of the following in a single response:

1. **models.py** - SQLAlchemy models: User, Task, Project, Comment with relationships
2. **schemas.py** - Pydantic schemas for request/response validation
3. **database.py** - Database connection, session management, base model
4. **crud.py** - CRUD operations for all models
5. **main.py** - FastAPI app with all endpoints:
   - POST /users, GET /users, GET /users/{id}
   - POST /projects, GET /projects
   - POST /projects/{id}/tasks, GET /tasks, PUT /tasks/{id}, DELETE /tasks/{id}
   - POST /tasks/{id}/comments
6. **auth.py** - Simple JWT authentication middleware
7. **requirements.txt**

Use proper error handling, status codes, and pagination. Each file should be complete and runnable.

Format each file as:
```python:filename.py
<code>
```""",
        expected_keywords=["models.py", "schemas.py", "database.py", "crud.py", "main.py", "auth.py", "FastAPI", "SQLAlchemy", "Pydantic", "jwt", "requirements"],
        runnable=False,
        max_tokens=12288,
    ),
    TestCase(
        id="project_cli_tool",
        name="CLI Tool with Subcommands (Click)",
        dimension="project_generation",
        prompt="""Create a complete CLI tool project for managing a personal knowledge base. Include:

1. **cli.py** - Main CLI using Click with subcommands: add, search, list, delete, export, tag
2. **storage.py** - SQLite-based storage layer with full-text search (FTS5)
3. **models.py** - Data classes: Note, Tag, Notebook
4. **search.py** - Search engine with relevance scoring
5. **export.py** - Export to Markdown, JSON, HTML
6. **config.py** - Config management with TOML
7. **setup.py** - Package setup for pip install
8. **README.md** - Usage examples

Each file must be complete and production-quality. Format each file as:
```python:filename.py
<code>
```""",
        expected_keywords=["cli.py", "storage.py", "models.py", "search.py", "export.py", "config.py", "setup.py", "Click", "sqlite3", "FTS5", "README"],
        runnable=False,
        max_tokens=12288,
    ),
    # 7. Edge Cases / Robustness
    TestCase(
        id="edge_csv_parser",
        name="Robust CSV Parser with Edge Cases",
        dimension="robustness",
        prompt="""Write a robust CSV parser in Python that handles ALL of these edge cases:
1. Quoted fields with commas inside
2. Escaped quotes ("")
3. Fields with newlines inside quotes
4. BOM (byte order mark) handling
5. Different delimiters (comma, tab, semicolon, pipe)
6. Empty lines and trailing newlines
7. Inconsistent column counts
8. Unicode normalization
9. Streaming mode for large files (generator-based)
10. Custom quote characters
11. Auto-detect delimiter
12. Return typed records (list of dataclass or dict)

The parser should be a class RobustCSVParser with:
- __init__(self, delimiter=None, quotechar='"', encoding='utf-8')
- parse(self, source: str | Path | IO) -> Iterator[dict]
- parse_file(self, path: Path) -> list[dict]
- auto_detect_delimiter(self, sample: str) -> str

Include comprehensive docstrings and type hints.""",
        expected_keywords=["class RobustCSVParser", "BOM", "delimiter", "quotechar", "generator", "yield", "Iterator", "auto_detect", "Unicode"],
        max_tokens=8192,
    ),
    TestCase(
        id="edge_http_retry",
        name="HTTP Client with Circuit Breaker",
        dimension="robustness",
        prompt="""Implement an HTTP client wrapper with circuit breaker pattern in Python:
1. CircuitBreaker states: CLOSED, OPEN, HALF_OPEN
2. Configurable failure threshold, recovery timeout
3. HTTPClient class wrapping httpx or requests
4. Automatic retry with exponential backoff
5. Fallback response support
6. Metrics: total_requests, failures, circuit_state, time_in_state
7. Thread-safe state transitions
8. Context manager support
9. Custom exception classes: CircuitOpenError, MaxRetriesExceeded
10. Full type hints and docstrings

Provide complete, production-ready code.""",
        expected_keywords=["CircuitBreaker", "CLOSED", "OPEN", "HALF_OPEN", "httpx", "backoff", "CircuitOpenError", "MaxRetriesExceeded", "Lock"],
        max_tokens=8192,
    ),
]


# -- Scoring Logic ------------------------------------------------------


@dataclass
class TestResult:
    """Result of a single model x test-case evaluation."""

    model: str
    test_id: str
    test_name: str
    dimension: str
    success: bool
    elapsed: float
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0
    content_length: int = 0
    keyword_score: float = 0.0
    syntax_ok: bool = False
    syntax_error: str | None = None
    code_blocks: int = 0
    error: str | None = None
    response_snippet: str = ""
    raw_content: str = ""

    def score(self) -> float:
        """Compute a composite 0-100 score."""
        s = 0.0
        # Success (10 pts)
        if self.success:
            s += 10
        # Keyword coverage (30 pts)
        s += self.keyword_score * 30
        # Syntax (30 pts) - only for runnable code
        if self.syntax_ok:
            s += 30
        elif not self.raw_content:
            s += 0
        else:
            # partial credit if there are code blocks but syntax failed
            s += min(self.code_blocks * 5, 15)
        # Output volume / completeness (15 pts)
        if self.output_tokens > 0:
            s += min(self.output_tokens / 500, 15)
        # Reasoning depth (15 pts)
        if self.reasoning_tokens > 0:
            s += min(self.reasoning_tokens / 1000, 15)
        return round(min(s, 100.0), 1)


def extract_code_blocks(text: str) -> list[tuple[str, str]]:
    """Extract fenced code blocks. Returns list of (lang, code)."""
    pattern = r"```(\w*)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [(lang or "python", code) for lang, code in matches]


def check_syntax(code: str, lang: str = "python") -> tuple[bool, str | None]:
    """Check if code compiles. Returns (ok, error_message)."""
    if lang not in ("python", "py", "python3", ""):
        return True, None  # skip non-python
    try:
        compile(code, "<benchmark>", "exec")
        return True, None
    except SyntaxError as e:
        return False, f"{e.__class__.__name__}: {e.msg} (line {e.lineno})"


def score_keywords(content: str, keywords: list[str]) -> float:
    """Score how many expected keywords appear in the content (0.0-1.0)."""
    if not keywords:
        return 1.0
    found = sum(1 for kw in keywords if kw.lower() in content.lower())
    return found / len(keywords)


def call_model(model: str, prompt: str, max_tokens: int) -> dict:
    """Call a model and return raw results."""
    llm = ChatOpenAI(
        model=model,
        base_url=BASE_URL,
        api_key=API_KEY,
        streaming=False,
        stream_usage=True,
        timeout=TIMEOUT,
        max_tokens=max_tokens,
    )
    start = time.time()
    resp = llm.invoke(prompt)
    elapsed = time.time() - start

    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    usage = resp.usage_metadata or {}

    return {
        "content": content,
        "elapsed": elapsed,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "reasoning_tokens": (
            usage.get("output_token_details", {}).get("reasoning", 0)
            if usage.get("output_token_details")
            else 0
        ),
        "response_metadata": resp.response_metadata,
    }


def evaluate(model: str, tc: TestCase) -> TestResult:
    """Run one test case on one model and evaluate."""
    result = TestResult(
        model=model,
        test_id=tc.id,
        test_name=tc.name,
        dimension=tc.dimension,
        success=False,
        elapsed=0.0,
    )

    try:
        raw = call_model(model, tc.prompt, tc.max_tokens)
        result.raw_content = raw["content"]
        result.elapsed = raw["elapsed"]
        result.input_tokens = raw["input_tokens"]
        result.output_tokens = raw["output_tokens"]
        result.total_tokens = raw["total_tokens"]
        result.reasoning_tokens = raw["reasoning_tokens"]
        result.content_length = len(raw["content"])
        result.response_snippet = raw["content"][:500]
        result.success = True

        # Keyword score
        result.keyword_score = score_keywords(raw["content"], tc.expected_keywords)

        # Extract and check code blocks
        blocks = extract_code_blocks(raw["content"])
        result.code_blocks = len(blocks)

        if tc.runnable and blocks:
            # Check syntax of the largest python block
            python_blocks = [(l, c) for l, c in blocks if l in ("python", "py", "")]
            if python_blocks:
                largest = max(python_blocks, key=lambda x: len(x[1]))
                ok, err = check_syntax(largest[1], largest[0])
                result.syntax_ok = ok
                result.syntax_error = err
            else:
                # No python-tagged blocks, try all
                largest = max(blocks, key=lambda x: len(x[1]))
                ok, err = check_syntax(largest[1], largest[0])
                result.syntax_ok = ok
                result.syntax_error = err
        elif not tc.runnable:
            # Non-runnable: syntax check is N/A, give credit
            result.syntax_ok = True

    except Exception as e:
        result.error = f"{e.__class__.__name__}: {e}"
        result.response_snippet = traceback.format_exc()[:500]

    return result


# -- Report Generation --------------------------------------------------


def generate_report(results: list[TestResult], output_path: Path) -> None:
    """Generate a Markdown report from results."""
    lines = []
    lines.append("# Volcengine (Huoshan) Model Coding Benchmark Report")
    lines.append("")
    lines.append(f"- Models tested: {len(MODELS)}")
    lines.append(f"- Test cases: {len(TEST_CASES)}")
    lines.append(f"- Total evaluations: {len(results)}")
    lines.append(f"- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Per-model summary
    lines.append("## Per-Model Summary")
    lines.append("")
    lines.append("| Model | Avg Score | Avg Elapsed | Avg Output Tokens | Avg Reasoning | Success Rate | Syntax Pass Rate |")
    lines.append("|-------|-----------|-------------|-------------------|---------------|--------------|------------------|")

    model_stats = {}
    for r in results:
        if r.model not in model_stats:
            model_stats[r.model] = {
                "scores": [], "elapsed": [], "output": [], "reasoning": [],
                "success": 0, "syntax_ok": 0, "total": 0,
            }
        ms = model_stats[r.model]
        ms["scores"].append(r.score())
        ms["elapsed"].append(r.elapsed)
        ms["output"].append(r.output_tokens)
        ms["reasoning"].append(r.reasoning_tokens)
        ms["total"] += 1
        if r.success:
            ms["success"] += 1
        if r.syntax_ok:
            ms["syntax_ok"] += 1

    for model in MODELS:
        ms = model_stats.get(model)
        if not ms or ms["total"] == 0:
            lines.append(f"| {model} | N/A | N/A | N/A | N/A | N/A | N/A |")
            continue
        avg_score = sum(ms["scores"]) / len(ms["scores"])
        avg_elapsed = sum(ms["elapsed"]) / len(ms["elapsed"])
        avg_output = sum(ms["output"]) / len(ms["output"])
        avg_reasoning = sum(ms["reasoning"]) / len(ms["reasoning"])
        success_rate = ms["success"] / ms["total"] * 100
        syntax_rate = ms["syntax_ok"] / ms["total"] * 100
        lines.append(
            f"| {model} | {avg_score:.1f} | {avg_elapsed:.1f}s | {avg_output:.0f} | {avg_reasoning:.0f} | {success_rate:.0f}% | {syntax_rate:.0f}% |"
        )
    lines.append("")

    # Per-dimension breakdown
    lines.append("## Per-Dimension Breakdown")
    lines.append("")
    dimensions = sorted(set(tc.dimension for tc in TEST_CASES))
    for dim in dimensions:
        lines.append(f"### {dim.replace('_', ' ').title()}")
        lines.append("")
        lines.append("| Model | Test | Score | Elapsed | Output Tokens | Syntax | Keywords |")
        lines.append("|-------|------|-------|---------|---------------|--------|----------|")
        dim_results = [r for r in results if r.dimension == dim]
        for r in sorted(dim_results, key=lambda x: MODELS.index(x.model)):
            syntax_str = "PASS" if r.syntax_ok else f"FAIL: {r.syntax_error or ''}"
            lines.append(
                f"| {r.model} | {r.test_name} | {r.score()} | {r.elapsed:.1f}s | {r.output_tokens} | {syntax_str} | {r.keyword_score*100:.0f}% |"
            )
        lines.append("")

    # Detailed errors
    errors = [r for r in results if r.error]
    if errors:
        lines.append("## Errors")
        lines.append("")
        for r in errors:
            lines.append(f"### {r.model} - {r.test_name}")
            lines.append(f"```\n{r.error}\n```")
            lines.append("")

    output_path.write_text("\n".join(lines))
    print(f"Report written to {output_path}")


# -- Main ---------------------------------------------------------------


def main() -> int:
    """Run benchmark with parallel model evaluations."""
    import concurrent.futures

    if not API_KEY:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        return 1

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    total = len(MODELS) * len(TEST_CASES)
    json_path = Path(f"scripts/benchmark_results_{timestamp}.json")
    report_path = Path(f"scripts/benchmark_report_{timestamp}.md")

    print(f"Starting benchmark: {len(MODELS)} models x {len(TEST_CASES)} tests = {total} evaluations")
    print(f"Parallel workers: 3")
    print(f"Estimated time: ~{total * 160 / 3 / 60:.0f} minutes (at ~160s per call, 3 concurrent)")
    print()

    # Build all (model, test_case) pairs
    tasks = [(model, tc) for model in MODELS for tc in TEST_CASES]
    results: list[TestResult] = []
    completed = 0
    lock = __import__("threading").Lock()

    def save_intermediate() -> None:
        """Save intermediate results to JSON."""
        with lock:
            json_data = [asdict(r) for r in sorted(results, key=lambda x: (MODELS.index(x.model) if x.model in MODELS else 99, x.test_id))]
            json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False, default=str))

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(evaluate, model, tc): (model, tc)
            for model, tc in tasks
        }

        for future in concurrent.futures.as_completed(future_to_task):
            model, tc = future_to_task[future]
            completed += 1
            try:
                r = future.result()
            except Exception as e:
                r = TestResult(
                    model=model, test_id=tc.id, test_name=tc.name,
                    dimension=tc.dimension, success=False, elapsed=0.0,
                    error=f"{e.__class__.__name__}: {e}",
                )
            with lock:
                results.append(r)

            status = "OK" if r.success else "FAIL"
            print(
                f"[{completed}/{total}] {model} :: {tc.name} ... "
                f"{status}  score={r.score()}  elapsed={r.elapsed:.1f}s  "
                f"tokens={r.output_tokens}  err={r.error or ''}",
                flush=True,
            )

            # Save intermediate results every 5 completions
            if completed % 5 == 0:
                save_intermediate()

    # Final save and report
    save_intermediate()
    generate_report(results, report_path)

    print(f"\nDone! Results: {json_path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())