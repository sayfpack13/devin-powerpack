"""Deterministic Raft consensus simulation (Python standard library only).

Implements the Raft protocol per the original paper (Ongaro & Ousterhout):
  * Follower / Candidate / Leader roles with randomized election timeouts.
  * RequestVote quorum elections (> N/2 strict majority).
  * AppendEntries log replication with the log-matching invariant.
  * Leader commit advancement only on entries of the current term.
  * A deterministic Network router supporting partition() / heal().

Time is modeled in discrete ticks (1 tick ~ 1 ms of logical time). All
message delivery is deterministic: Network.deliver() drains the queue, and
Cluster.tick() advances every node's timers by one tick. A seeded RNG is
injected per node so election jitter is reproducible across runs.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Dict, Iterable, List, Optional, Tuple

ELECTION_TIMEOUT_MIN = 150  # ticks
ELECTION_TIMEOUT_MAX = 300  # ticks
HEARTBEAT_INTERVAL = 50     # ticks, must be < ELECTION_TIMEOUT_MIN

NO_OP = ""  # command appended by a new leader to anchor its term


class State(Enum):
    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"
    LEADER = "LEADER"


@dataclass(frozen=True)
class LogEntry:
    term: int
    command: str


# --------------------------------------------------------------------------
# RPC messages
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RequestVote:
    term: int
    candidate_id: int
    last_log_index: int
    last_log_term: int


@dataclass(frozen=True)
class RequestVoteResponse:
    term: int
    vote_granted: bool


@dataclass(frozen=True)
class AppendEntries:
    term: int
    leader_id: int
    prev_log_index: int
    prev_log_term: int
    entries: Tuple[LogEntry, ...]
    leader_commit: int


@dataclass(frozen=True)
class AppendEntriesResponse:
    term: int
    success: bool
    match_index: int = 0   # highest log index known to match the leader
    last_index: int = 0    # follower's last log index (fast next_index backoff)


# --------------------------------------------------------------------------
# Network: deterministic router with partition support
# --------------------------------------------------------------------------


class Network:
    """FIFO message router.

    Messages are queued by send()/broadcast() and delivered by deliver().
    partition(a, b) blocks all traffic between the two groups; messages sent
    across a cut (including in-flight ones) are dropped. heal() restores
    full connectivity.
    """

    def __init__(self) -> None:
        self.nodes: Dict[int, "RaftNode"] = {}
        self._queue: Deque[Tuple[int, int, object]] = deque()
        self._blocked: set = set()
        self.delivered_count = 0
        self.dropped_count = 0

    def register(self, node: "RaftNode") -> None:
        self.nodes[node.id] = node

    def connected(self, a: int, b: int) -> bool:
        return frozenset((a, b)) not in self._blocked

    def send(self, src: int, dst: int, msg: object) -> None:
        if self.connected(src, dst):
            self._queue.append((dst, src, msg))
        else:
            self.dropped_count += 1

    def broadcast(self, src: int, peers: Iterable[int], msg: object) -> None:
        for p in peers:
            self.send(src, p, msg)

    def partition(self, group_a: Iterable[int], group_b: Iterable[int]) -> None:
        for a in group_a:
            for b in group_b:
                self._blocked.add(frozenset((a, b)))

    def heal(self) -> None:
        self._blocked.clear()

    @property
    def partitioned(self) -> bool:
        return bool(self._blocked)

    def deliver(self) -> None:
        """Deliver every queued message; messages generated during delivery
        are delivered in the same pass (instant RPC round-trips per tick)."""
        while self._queue:
            dst, src, msg = self._queue.popleft()
            if dst not in self.nodes or not self.connected(src, dst):
                self.dropped_count += 1
            else:
                self.delivered_count += 1
                self.nodes[dst].receive(msg, src)


# --------------------------------------------------------------------------
# Raft node
# --------------------------------------------------------------------------


class RaftNode:
    def __init__(
        self,
        node_id: int,
        peer_ids: Iterable[int],
        network: Network,
        rng: Optional[random.Random] = None,
    ) -> None:
        self.id = node_id
        self.peers = sorted(peer_ids)
        self.cluster_size = len(self.peers) + 1
        self.network = network
        self.rng = rng or random.Random()

        # Persistent state (Raft paper, Fig. 2)
        self.current_term = 0
        self.voted_for: Optional[int] = None
        self.log: List[LogEntry] = []  # entry i lives at self.log[i-1]

        # Volatile state
        self.state = State.FOLLOWER
        self.leader_id: Optional[int] = None
        self.commit_index = 0
        self.last_applied = 0
        self.state_machine: Dict[str, str] = {}
        self.votes_received: set = set()

        # Leader volatile state
        self.next_index: Dict[int, int] = {}
        self.match_index: Dict[int, int] = {}

        # Timers, in ticks
        self.elapsed = 0
        self.election_timeout = self._new_election_timeout()
        self.hb_elapsed = 0

    # -- log helpers -----------------------------------------------------

    def _new_election_timeout(self) -> int:
        return self.rng.randint(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)

    def _reset_election_timer(self) -> None:
        self.elapsed = 0
        self.election_timeout = self._new_election_timeout()

    def last_log_index(self) -> int:
        return len(self.log)

    def last_log_term(self) -> int:
        return self.log[-1].term if self.log else 0

    def term_at(self, index: int) -> int:
        if 0 < index <= len(self.log):
            return self.log[index - 1].term
        return 0

    def quorum(self, count: int) -> bool:
        return count > self.cluster_size // 2

    # -- timers ----------------------------------------------------------

    def on_tick(self) -> None:
        if self.state is State.LEADER:
            self.hb_elapsed += 1
            if self.hb_elapsed >= HEARTBEAT_INTERVAL:
                self.hb_elapsed = 0
                self._send_append_entries_to_all()
        else:
            self.elapsed += 1
            if self.elapsed >= self.election_timeout:
                self._start_election()

    # -- elections --------------------------------------------------------

    def _start_election(self) -> None:
        self.state = State.CANDIDATE
        self.current_term += 1
        self.voted_for = self.id
        self.votes_received = {self.id}
        self.leader_id = None
        self._reset_election_timer()
        if self.quorum(len(self.votes_received)):
            self._become_leader()
            return
        self.network.broadcast(
            self.id,
            self.peers,
            RequestVote(
                term=self.current_term,
                candidate_id=self.id,
                last_log_index=self.last_log_index(),
                last_log_term=self.last_log_term(),
            ),
        )

    def _become_leader(self) -> None:
        self.state = State.LEADER
        self.leader_id = self.id
        last = self.last_log_index()
        self.next_index = {p: last + 1 for p in self.peers}
        self.match_index = {p: 0 for p in self.peers}
        self.hb_elapsed = 0
        # Anchor commitment with a no-op entry in the new term so entries
        # from prior terms become committable once it is replicated.
        self.log.append(LogEntry(self.current_term, NO_OP))
        self._send_append_entries_to_all()

    def _step_down(self, term: int) -> None:
        self.current_term = term
        self.state = State.FOLLOWER
        self.voted_for = None
        self.votes_received.clear()
        self.leader_id = None

    # -- log replication ---------------------------------------------------

    def _send_append_entries_to_all(self) -> None:
        for p in self.peers:
            self._send_append_entries(p)

    def _send_append_entries(self, peer: int) -> None:
        next_i = self.next_index[peer]
        prev_index = next_i - 1
        self.network.send(
            self.id,
            peer,
            AppendEntries(
                term=self.current_term,
                leader_id=self.id,
                prev_log_index=prev_index,
                prev_log_term=self.term_at(prev_index),
                entries=tuple(self.log[prev_index:]),
                leader_commit=self.commit_index,
            ),
        )

    def _advance_commit(self) -> None:
        """Advance commit_index to the highest N replicated on a majority,
        restricted to entries of the current term (Raft safety rule)."""
        for n in range(self.last_log_index(), self.commit_index, -1):
            if self.log[n - 1].term != self.current_term:
                continue
            replicated = 1  # the leader itself
            for p in self.peers:
                if self.match_index.get(p, 0) >= n:
                    replicated += 1
            if self.quorum(replicated):
                self.commit_index = n
                break
        self._apply_committed()

    def _apply_committed(self) -> None:
        while self.last_applied < self.commit_index:
            entry = self.log[self.last_applied]
            self.last_applied += 1
            if entry.command and "=" in entry.command:
                key, value = entry.command.split("=", 1)
                self.state_machine[key] = value

    # -- client API --------------------------------------------------------

    def submit(self, command: str) -> int:
        """Append a client command; returns its 1-based log index."""
        if self.state is not State.LEADER:
            raise RuntimeError(
                f"node {self.id} is {self.state.value}, not leader "
                f"(leader is {self.leader_id})"
            )
        self.log.append(LogEntry(self.current_term, command))
        self._send_append_entries_to_all()
        return self.last_log_index()

    # -- RPC handlers --------------------------------------------------------

    def receive(self, msg: object, src: int) -> None:
        if isinstance(msg, RequestVote):
            self._on_request_vote(msg, src)
        elif isinstance(msg, RequestVoteResponse):
            self._on_request_vote_response(msg, src)
        elif isinstance(msg, AppendEntries):
            self._on_append_entries(msg, src)
        elif isinstance(msg, AppendEntriesResponse):
            self._on_append_entries_response(msg, src)

    def _on_request_vote(self, msg: RequestVote, src: int) -> None:
        grant = False
        if msg.term >= self.current_term:
            if msg.term > self.current_term:
                self._step_down(msg.term)
            up_to_date = (msg.last_log_term, msg.last_log_index) >= (
                self.last_log_term(),
                self.last_log_index(),
            )
            if up_to_date and self.voted_for in (None, msg.candidate_id):
                grant = True
                self.voted_for = msg.candidate_id
                self._reset_election_timer()
        self.network.send(
            self.id, src,
            RequestVoteResponse(term=self.current_term, vote_granted=grant),
        )

    def _on_request_vote_response(self, msg: RequestVoteResponse, src: int) -> None:
        if msg.term > self.current_term:
            self._step_down(msg.term)
            return
        if self.state is not State.CANDIDATE or msg.term != self.current_term:
            return
        if msg.vote_granted:
            self.votes_received.add(src)
            if self.quorum(len(self.votes_received)):
                self._become_leader()

    def _on_append_entries(self, msg: AppendEntries, src: int) -> None:
        success = False
        if msg.term >= self.current_term:
            if msg.term > self.current_term:
                self._step_down(msg.term)
            elif self.state is not State.FOLLOWER:
                # A valid leader exists for our term; stand down.
                self.state = State.FOLLOWER
            self.leader_id = msg.leader_id
            self.elapsed = 0  # heartbeat heard

            if msg.prev_log_index == 0 or (
                self.term_at(msg.prev_log_index) == msg.prev_log_term
            ):
                success = True
                i = msg.prev_log_index
                for entry in msg.entries:
                    i += 1
                    if i <= len(self.log):
                        if self.log[i - 1].term != entry.term:
                            del self.log[i - 1:]  # truncate conflicting tail
                            self.log.append(entry)
                    else:
                        self.log.append(entry)
                if msg.leader_commit > self.commit_index:
                    self.commit_index = min(
                        msg.leader_commit, self.last_log_index()
                    )
                    self._apply_committed()

        self.network.send(
            self.id,
            src,
            AppendEntriesResponse(
                term=self.current_term,
                success=success,
                match_index=msg.prev_log_index + len(msg.entries)
                if success else 0,
                last_index=self.last_log_index(),
            ),
        )

    def _on_append_entries_response(
        self, msg: AppendEntriesResponse, src: int
    ) -> None:
        if msg.term > self.current_term:
            self._step_down(msg.term)
            return
        if self.state is not State.LEADER or msg.term != self.current_term:
            return
        if msg.success:
            self.match_index[src] = max(
                self.match_index.get(src, 0), msg.match_index
            )
            self.next_index[src] = self.match_index[src] + 1
            self._advance_commit()
        else:
            # Log-matching probe failed: back next_index off (jumping to
            # last_index+1 when the follower log is shorter) and retry.
            self.next_index[src] = max(
                1, min(self.next_index[src] - 1, msg.last_index + 1)
            )
            self._send_append_entries(src)


# --------------------------------------------------------------------------
# Cluster driver
# --------------------------------------------------------------------------


class Cluster:
    """Owns the Network and all nodes; tick() advances the simulation."""

    def __init__(self, size: int = 5, seed: int = 0) -> None:
        self.network = Network()
        self.nodes: Dict[int, RaftNode] = {}
        self.time = 0
        for i in range(size):
            peers = [j for j in range(size) if j != i]
            node = RaftNode(
                i, peers, self.network,
                rng=random.Random(f"cluster:{seed}:node:{i}"),
            )
            self.nodes[i] = node
            self.network.register(node)

    def tick(self, n: int = 1) -> None:
        for _ in range(n):
            self.time += 1
            self.network.deliver()
            for node in self.nodes.values():
                node.on_tick()

    def partition(self, group_a: Iterable[int], group_b: Iterable[int]) -> None:
        self.network.partition(group_a, group_b)

    def heal(self) -> None:
        self.network.heal()

    def leaders(self) -> List[RaftNode]:
        return [n for n in self.nodes.values() if n.state is State.LEADER]

    def leader(self) -> Optional[RaftNode]:
        found = self.leaders()
        return found[0] if found else None

    def wait_for_leader(
        self, max_ticks: int = 1000, among: Optional[Iterable[int]] = None
    ) -> Optional[RaftNode]:
        """Tick until some node (optionally restricted to `among`) leads."""
        pool = (self.nodes[i] for i in among) if among is not None else None
        for _ in range(max_ticks):
            self.tick()
            for node in (pool or self.nodes.values()):
                if node.state is State.LEADER:
                    return node
            if pool is not None:
                pool = (self.nodes[i] for i in among)
        return None

    def submit(self, command: str) -> int:
        leader = self.leader()
        if leader is None:
            raise RuntimeError("no leader available")
        return leader.submit(command)
