# Challenge 05: Distributed Raft Consensus Engine (Leader Election & Partition Tolerance)

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
