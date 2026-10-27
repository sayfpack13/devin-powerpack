import os
import shutil
import struct
import time

powerpack_root = os.path.dirname(os.path.abspath(__file__))
ws_root = os.path.join(powerpack_root, "workspaces")


# Ensure workspaces root exists without wiping existing solutions
os.makedirs(ws_root, exist_ok=True)

models = ["swe_medium", "swe_high"]

# =====================================================================
# Challenge 1: Sliding Window Rate Limiter (Concurrency & Memory Bounds)
# =====================================================================
c1_task = """# Challenge 01: Thread-Safe Sliding Window Rate Limiter

## Objective
Build a lightweight, thread-safe, high-concurrency Sliding Window Rate Limiter in Python with bounded memory consumption and zero external dependencies.

## Instructions:
Paste the prompt below into Devin chat:

```markdown
Initialize this clean workspace using devin-state-init.

Build a thread-safe, high-concurrency Sliding Window Rate Limiter in Python (or Node.js) with zero external dependencies.

Requirements:
1. Core API:
   - RateLimiter(max_requests: int, window_seconds: float)
   - allow_request(client_id: str) -> bool
   - get_remaining_allowance(client_id: str) -> int
   - reset(client_id: str) -> None
2. Performance & Memory Mandates (Mythos v3.0):
   - Memory MUST be bounded: Expired timestamps must be purged lazily or via a ring-buffer/deque so memory does not leak over hours.
   - Use First-Principles & Occam's Razor: Do NOT store unbounded timestamp lists; use a sliding deque or ring-buffer with minimal diff.
   - Thread safety: Use threading.Lock() appropriately for concurrent calls.
3. Automated Testing & Verification:
   - Build a unittest suite covering:
     * Burst allowance within window limit
     * Rejection once max_requests is exceeded
     * Window sliding allowing new requests after elapsed time
     * Multi-client isolation (client A does not exhaust client B)
     * High-concurrency test using concurrent.futures
   - Profile the test with devin-bench to prove memory bounds.
   - Output exact exit code 0 evidence.
```
"""

for m in models:
    dir_path = os.path.join(ws_root, "challenge_01_rate_limiter", m)
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, "TASK.md"), "w", encoding="utf-8") as f:
        f.write(c1_task)

# =====================================================================
# Challenge 2: Protocol Reversing & Packet Unpacker
# =====================================================================
# Generate real binary packet fixture:
packet_magic = 0xD371  # 2 bytes
packet_version = 1      # 1 byte
flags = 0x05           # 1 byte (compressed + encrypted flag)
payload_str = b"SECRET_INTERNAL_SESSION_TOKEN_XYZ987"
crc = 0xAA55
raw_packet = struct.pack(">HBB I Q", packet_magic, packet_version, flags, len(payload_str), int(time.time())) + payload_str + struct.pack(">H", crc)

c2_task = """# Challenge 02: Binary Protocol Reverse Engineering & Parser

## Objective
Analyze an unknown binary packet capture (`sample_capture.bin`), reverse-engineer the header structure, field offsets, and payload encoding, and construct a robust parser and validator.

## Instructions:
Paste the prompt below into Devin chat:

```markdown
Initialize this clean workspace using devin-state-init.

We captured a raw binary packet in `sample_capture.bin`. 
Use the reverse_engineer subagent and Mythos v3.0 reverse engineering protocols:

1. Reverse-Engineer the Binary Layout:
   - Do NOT dump raw bytes into context. Use python or hex inspection to extract field offsets.
   - Identify header fields: Magic bytes, Version, Flags, Payload Length, 64-bit Timestamp, and trailing Checksum.
   - Document the protocol schema in `.mythos/re_symbols.md`.
2. Construct Parser & Serializer:
   - Build `protocol.py` with `Packet.unpack(raw_bytes)` and `Packet.pack()`.
   - Validate magic bytes and payload checksum.
3. Automated Testing & Verification:
   - Write `test_protocol.py` testing serialization, deserialization, invalid magic byte handling, and corrupt payload rejection.
   - Run tests and provide exact exit code 0 evidence.
```
"""

for m in models:
    dir_path = os.path.join(ws_root, "challenge_02_protocol_reverser", m)
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, "TASK.md"), "w", encoding="utf-8") as f:
        f.write(c2_task)
    with open(os.path.join(dir_path, "sample_capture.bin"), "wb") as f:
        f.write(raw_packet)

# =====================================================================
# Challenge 3: O(1) Concurrent LRU Cache with TTL
# =====================================================================
c3_task = """# Challenge 03: O(1) Concurrent LRU Cache with TTL & Eviction

## Objective
Build a production-grade, thread-safe LRU (Least Recently Used) cache with O(1) get/set complexity, TTL expiration, and exact capacity enforcement using standard library primitives.

## Instructions:
Paste the prompt below into Devin chat:

```markdown
Initialize this clean workspace using devin-state-init.

Build a thread-safe, high-concurrency LRU Cache with TTL support in Python.

Requirements:
1. Core API:
   - LRUCache(capacity: int, default_ttl_seconds: float = None)
   - get(key: str) -> Any (moves to most recently used)
   - put(key: str, value: Any, ttl_seconds: float = None)
   - evict_expired() -> int
   - size() -> int
2. Performance & Memory Mandates (Mythos v3.0):
   - O(1) Get and Put operations (use OrderedDict or doubly linked list + hash map).
   - Strict capacity limit: Never exceed capacity items; evict least recently used upon insertion.
   - Run devin-bench on the implementation to verify CPU time and peak RAM.
3. Automated Testing & Verification:
   - Write comprehensive tests for LRU eviction order, TTL expiration, thread-safety under 50 concurrent threads, and non-existent key handling.
   - Execute tests and output exit code 0 evidence.
```
"""

for m in models:
    dir_path = os.path.join(ws_root, "challenge_03_lru_cache_perf", m)
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, "TASK.md"), "w", encoding="utf-8") as f:
        f.write(c3_task)

# =====================================================================
# Challenge 4: In-Memory KV Store with Transactions & TTL
# =====================================================================
c4_task = """# Challenge 04: In-Memory Key-Value Store with Nested Atomic Transactions & TTL

## Objective
Build a lightweight, production-grade In-Memory Key-Value Store with TTL (Time-To-Live) and Atomic Transactions in Python (or Node.js).

## Instructions:
Paste the prompt below into Devin chat:

```markdown
Initialize this clean workspace using devin-state-init.

Build a lightweight, production-grade In-Memory Key-Value Store with TTL (Time-To-Live) and Atomic Transactions in Python (or Node.js).

Requirements:
1. Core Operations: SET(key, value, ttl_seconds?), GET(key), DELETE(key).
2. Transaction Support: 
   - BEGIN: Starts a transaction.
   - COMMIT: Commits changes atomically.
   - ROLLBACK: Reverts all changes made since BEGIN. Supports at least 2 levels of nested transactions.
3. Architecture & Intelligence:
   - Use First-Principles & Occam's Razor: Do NOT install external packages; write clean, idiomatic code using standard library primitives with the smallest possible diff.
4. Automated Testing & Proof of Accuracy:
   - Build an automated test suite covering:
     * Basic GET/SET/DELETE
     * TTL key expiration
     * Transaction commit
     * Transaction rollback (including nested rollback)
     * Edge cases (getting non-existent key, committing without BEGIN)
   - Execute the test suite and provide the exact terminal output demonstrating that all assertions pass with exit code 0.
```
"""

for m in models:
    dir_path = os.path.join(ws_root, "challenge_04_kvstore_txns", m)
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, "TASK.md"), "w", encoding="utf-8") as f:
        f.write(c4_task)

# =====================================================================
# Challenge 5: Distributed Raft Consensus Engine
# =====================================================================
c5_task = """# Challenge 05: Distributed Raft Consensus Engine (Leader Election & Partition Tolerance)

## Objective
Build a lightweight, production-grade Distributed Raft Consensus Cluster simulation in Python (stdlib only) capable of surviving network partitions, split-vote deadlocks, and log desynchronization.

## Instructions:
Paste the prompt below into Devin chat:

```markdown
Initialize this clean workspace using devin-state-init.

Build a lightweight, production-grade Distributed Raft Consensus Cluster simulation in Python (standard library only) capable of surviving network partitions, split votes, and log desynchronization according to the Raft protocol specification.

Architecture & Functional Requirements:
1. Raft Node Roles & States:
   - Every node has one of three states: Follower, Candidate, or Leader.
   - Randomized election timeout jitter (e.g. 150ms-300ms) to avoid simultaneous candidate splits.
   - Periodic heartbeats from the Leader to keep followers in Follower state.
2. Quorum & Leader Election:
   - RequestVote RPC: Candidate increments term, votes for itself, and broadcasts RequestVote to peers.
   - Candidate transitions to Leader if and only if it receives votes from a strict majority quorum (> N/2).
   - Any node receiving an RPC with a higher term must immediately step down to Follower and update its term.
3. Log Replication & Commit Safety:
   - AppendEntries RPC: Leader sends log entries to followers with heartbeats.
   - A log entry is committed only when replicated on a majority of cluster nodes.
   - Log Matching Invariant: Follower rejects AppendEntries if prev_log_index/prev_log_term does not match, causing leader to decrement next_index and repair follower logs.
4. Network Partition & Split-Brain Tolerance:
   - A deterministic network simulator or cluster router with `partition(group_a, group_b)` and `heal()`.
   - Minority partition (e.g., 2 nodes out of 5) CANNOT elect a leader and CANNOT commit entries.
   - Majority partition (e.g., 3 nodes out of 5) elects a leader and successfully commits entries.
   - On `heal()`, partitioned nodes must accept the true leader's log, truncate any uncommitted speculative entries, and synchronize their state machines identically.
5. Automated Verification & Adversarial Stress Tests:
   - Create `test_raft.py` with rigorous tests covering:
     * Fast initial leader election on cluster startup.
     * Heartbeats suppressing unnecessary elections.
     * Successful log replication and majority commit.
     * Network partition isolation: minority cannot commit, majority continues committing.
     * Partition healing: log truncation and state machine convergence across all 5 nodes.
     * Higher term step-down behavior.
   - Execute the test suite and verify 100% passing tests with exit code 0.
   - Profile execution using devin-bench or performance metrics.
```
"""

for m in models:
    dir_path = os.path.join(ws_root, "challenge_05_raft_consensus", m)
    os.makedirs(dir_path, exist_ok=True)
    task_file = os.path.join(dir_path, "TASK.md")
    if not os.path.exists(task_file):
        with open(task_file, "w", encoding="utf-8") as f:
            f.write(c5_task)

print("All structured challenge workspaces generated successfully!")
