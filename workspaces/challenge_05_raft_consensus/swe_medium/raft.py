"""Lightweight Raft consensus simulation (stdlib only).

Deterministic synchronous model: a virtual millisecond clock drives election
timeouts and heartbeats; RPCs are delivered synchronously through a
partitionable Network router. Log entries are (term, command) tuples;
committed commands are applied to a per-node state machine (a list).
"""

import random
from dataclasses import dataclass, field

FOLLOWER, CANDIDATE, LEADER = "follower", "candidate", "leader"

HEARTBEAT_INTERVAL = 50          # ms
ELECTION_TIMEOUT_MIN = 150       # ms
ELECTION_TIMEOUT_MAX = 300       # ms


@dataclass
class Entry:
    term: int
    command: object


class Network:
    """Router with symmetric partition support."""

    def __init__(self):
        self._blocked = set()  # frozenset({a, b}) pairs that cannot communicate

    def partition(self, group_a, group_b):
        for a in group_a:
            for b in group_b:
                if a != b:
                    self._blocked.add(frozenset((a, b)))

    def heal(self):
        self._blocked.clear()

    def can_send(self, src, dst):
        return frozenset((src, dst)) not in self._blocked


class Node:
    def __init__(self, node_id, peers, network, rng):
        self.id = node_id
        self.peers = peers          # list of other node ids
        self.network = network
        self.rng = rng

        self.state = FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log = []               # list[Entry]; index 0 == raft index 1
        self.commit_index = 0
        self.last_applied = 0
        self.state_machine = []     # applied commands, in order

        # leader state
        self.next_index = {}        # peer -> next log index to send (1-based)
        self.match_index = {}       # peer -> highest replicated index
        self.votes_received = set()

        self.now = 0
        self.election_deadline = 0
        self.next_heartbeat = 0
        self.cluster = None         # set by Cluster
        self._reset_election_deadline()

    # ---- helpers ------------------------------------------------------

    def _reset_election_deadline(self):
        self.election_deadline = self.now + self.rng.uniform(
            ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)

    def _last_index(self):
        return len(self.log)

    def _last_term(self):
        return self.log[-1].term if self.log else 0

    def _term_at(self, index):
        return self.log[index - 1].term if 1 <= index <= len(self.log) else 0

    def _majority(self):
        return (len(self.peers) + 1) // 2 + 1

    def _apply_committed(self):
        while self.last_applied < self.commit_index:
            self.state_machine.append(self.log[self.last_applied].command)
            self.last_applied += 1

    def _become_follower(self, term):
        self.state = FOLLOWER
        self.current_term = term
        self.voted_for = None
        self._reset_election_deadline()

    def _step_down_if_higher_term(self, term):
        if term > self.current_term:
            self._become_follower(term)
            return True
        return False

    def _node(self, nid):
        return self.cluster.nodes[nid]

    # ---- RPCs ---------------------------------------------------------

    def request_vote(self, term, candidate_id, last_log_index, last_log_term):
        if self._step_down_if_higher_term(term) or term == self.current_term:
            pass
        if term < self.current_term:
            return self.current_term, False
        up_to_date = (last_log_term > self._last_term() or
                      (last_log_term == self._last_term() and
                       last_log_index >= self._last_index()))
        if (self.voted_for in (None, candidate_id)) and up_to_date:
            self.voted_for = candidate_id
            self._reset_election_deadline()
            return self.current_term, True
        return self.current_term, False

    def append_entries(self, term, leader_id, prev_log_index, prev_log_term,
                       entries, leader_commit):
        if term < self.current_term:
            return self.current_term, False, self._last_index()
        self._step_down_if_higher_term(term)
        self.state = FOLLOWER
        self._reset_election_deadline()
        # log matching invariant
        if prev_log_index > self._last_index() or \
                self._term_at(prev_log_index) != prev_log_term:
            return self.current_term, False, self._last_index()
        # truncate conflicting entries and append new ones
        idx = prev_log_index
        for e in entries:
            idx += 1
            if idx <= self._last_index():
                if self._term_at(idx) != e.term:
                    del self.log[idx - 1:]
                    self.log.append(e)
            else:
                self.log.append(e)
        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, self._last_index())
            self._apply_committed()
        return self.current_term, True, self._last_index()

    # ---- leader actions -------------------------------------------------

    def _become_candidate(self):
        self.state = CANDIDATE
        self.current_term += 1
        self.voted_for = self.id
        self.votes_received = {self.id}
        self._reset_election_deadline()
        my_last_index, my_last_term = self._last_index(), self._last_term()
        for pid in self.peers:
            if not self.network.can_send(self.id, pid):
                continue
            peer = self._node(pid)
            term, granted = peer.request_vote(
                self.current_term, self.id, my_last_index, my_last_term)
            self._step_down_if_higher_term(term)
            if self.state != CANDIDATE:
                return
            if granted:
                self.votes_received.add(pid)
        if len(self.votes_received) >= self._majority():
            self._become_leader()

    def _become_leader(self):
        self.state = LEADER
        last = self._last_index()
        self.next_index = {p: last + 1 for p in self.peers}
        self.match_index = {p: 0 for p in self.peers}
        self.next_heartbeat = self.now  # heartbeat immediately
        self._replicate_all()

    def _replicate_to(self, pid):
        peer = self._node(pid)
        for _ in range(len(self.log) + 1):  # decrement next_index until match
            if self.state != LEADER:
                return
            ni = self.next_index[pid]
            prev_index = ni - 1
            prev_term = self._term_at(prev_index)
            entries = self.log[prev_index:]
            term, ok, peer_last = peer.append_entries(
                self.current_term, self.id, prev_index, prev_term,
                entries, self.commit_index)
            if self._step_down_if_higher_term(term):
                return
            if ok:
                self.match_index[pid] = max(self.match_index[pid],
                                            prev_index + len(entries))
                self.next_index[pid] = self.match_index[pid] + 1
                return
            self.next_index[pid] = max(1, ni - 1)
        self.next_index[pid] = 1

    def _replicate_all(self):
        for pid in self.peers:
            if self.network.can_send(self.id, pid):
                self._replicate_to(pid)
        self._advance_commit()

    def _advance_commit(self):
        for n in range(self._last_index(), self.commit_index, -1):
            if self._term_at(n) != self.current_term:
                continue
            count = 1 + sum(1 for p in self.peers
                            if self.match_index.get(p, 0) >= n)
            if count >= self._majority():
                self.commit_index = n
                self._apply_committed()
                break

    # ---- client API -----------------------------------------------------

    def submit(self, command):
        """Leader-only client write. Returns log index or None."""
        if self.state != LEADER:
            return None
        self.log.append(Entry(self.current_term, command))
        self._replicate_all()
        return self._last_index()

    # ---- tick -----------------------------------------------------------

    def tick(self, now):
        self.now = now
        if self.state == LEADER:
            if now >= self.next_heartbeat:
                self.next_heartbeat = now + HEARTBEAT_INTERVAL
                self._replicate_all()
        elif now >= self.election_deadline:
            self._become_candidate()


class Cluster:
    """Virtual-clock driver for a Raft cluster."""

    def __init__(self, n=5, seed=0):
        self.network = Network()
        self.nodes = {}
        ids = list(range(n))
        rng = random.Random(seed)
        for i in ids:
            node = Node(i, [p for p in ids if p != i], self.network,
                        random.Random(rng.random()))
            self.nodes[i] = node
        self.now = 0
        for node in self.nodes.values():
            node.cluster = self
            node._reset_election_deadline()

    def tick(self, step_ms=10):
        """Advance the virtual clock by one step."""
        self.now += step_ms
        for node in self.nodes.values():
            node.tick(self.now)

    def run(self, duration_ms, step_ms=10):
        for _ in range(0, duration_ms, step_ms):
            self.tick(step_ms)

    def run_until_leader(self, max_ms=5000, step_ms=10):
        for _ in range(0, max_ms, step_ms):
            self.tick(step_ms)
            leader = self.leader()
            if leader is not None:
                return leader
        return None

    def leader(self):
        leaders = [n for n in self.nodes.values() if n.state == LEADER]
        return leaders[0] if len(leaders) == 1 else None

    def leaders(self):
        return [n for n in self.nodes.values() if n.state == LEADER]

    def partition(self, group_a, group_b):
        self.network.partition(group_a, group_b)

    def heal(self):
        self.network.heal()
