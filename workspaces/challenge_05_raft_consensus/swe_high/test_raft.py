"""Rigorous verification suite for the Raft consensus simulation.

Run:  python test_raft.py        (or: python -m unittest test_raft -v)
All timing is in deterministic simulation ticks (1 tick ~ 1 ms).
"""

import random
import unittest

from raft import (
    AppendEntries,
    Cluster,
    ELECTION_TIMEOUT_MAX,
    RequestVote,
    State,
)


def log_tuple(node):
    """(term, command) sequence of a node's log, for equality checks."""
    return tuple((e.term, e.command) for e in node.log)


def wait_until(predicate, cluster, max_ticks, step=1):
    """Tick until predicate() is true; returns remaining ticks or raises."""
    for _ in range(max_ticks):
        if predicate():
            return
        cluster.tick(step)
    raise AssertionError("condition not met within tick budget")


class RaftTestBase(unittest.TestCase):
    def make_cluster(self, size=5, seed=7):
        return Cluster(size=size, seed=seed)

    def elect(self, cluster, max_ticks=1000, among=None):
        leader = cluster.wait_for_leader(max_ticks=max_ticks, among=among)
        self.assertIsNotNone(leader, "no leader elected")
        return leader

    def assert_converged(self, cluster, max_ticks=3000):
        """Every node's log, commit index and state machine must match."""
        wait_until(
            lambda: len({log_tuple(n) for n in cluster.nodes.values()}) == 1
            and len({n.commit_index for n in cluster.nodes.values()}) == 1,
            cluster,
            max_ticks,
        )
        logs = {log_tuple(n) for n in cluster.nodes.values()}
        sms = {
            tuple(sorted(n.state_machine.items()))
            for n in cluster.nodes.values()
        }
        self.assertEqual(len(logs), 1, "logs diverged")
        self.assertEqual(len(sms), 1, "state machines diverged")
        for node in cluster.nodes.values():
            self.assertEqual(node.commit_index, node.last_log_index())
            self.assertEqual(node.last_applied, node.commit_index)


class TestLeaderElection(RaftTestBase):
    def test_fast_initial_leader_election(self):
        cluster = self.make_cluster(seed=1)
        leader = self.elect(cluster, max_ticks=ELECTION_TIMEOUT_MAX + 50)
        self.assertIs(leader.state, State.LEADER)
        self.assertGreaterEqual(leader.current_term, 1)
        for node in cluster.nodes.values():
            if node.id != leader.id:
                self.assertIs(node.state, State.FOLLOWER)
                self.assertEqual(node.leader_id, leader.id)

    def test_election_requires_strict_majority(self):
        # A node alone in a 5-node cluster can never reach quorum.
        cluster = self.make_cluster(seed=2)
        cluster.partition({0}, {1, 2, 3, 4})
        for _ in range(ELECTION_TIMEOUT_MAX * 3):
            cluster.tick()
            self.assertIsNot(cluster.nodes[0].state, State.LEADER)

    def test_heartbeats_suppress_elections(self):
        cluster = self.make_cluster(seed=3)
        leader = self.elect(cluster)
        term = leader.current_term
        # Run far longer than the max election timeout: no new election
        # may occur while heartbeats flow.
        cluster.tick(ELECTION_TIMEOUT_MAX * 2)
        self.assertIs(cluster.nodes[leader.id].state, State.LEADER)
        for node in cluster.nodes.values():
            self.assertEqual(node.current_term, term)
            if node.id != leader.id:
                self.assertIs(node.state, State.FOLLOWER)

    def test_higher_term_forces_step_down(self):
        cluster = self.make_cluster(seed=4)
        leader = self.elect(cluster)
        peer = next(i for i in cluster.nodes if i != leader.id)
        higher = leader.current_term + 3
        # Direct RPC injection: a RequestVote carrying a higher term must
        # demote the leader regardless of the vote outcome.
        leader.receive(
            RequestVote(
                term=higher,
                candidate_id=peer,
                last_log_index=0,
                last_log_term=0,
            ),
            src=peer,
        )
        self.assertIs(leader.state, State.FOLLOWER)
        self.assertEqual(leader.current_term, higher)

        # Same for AppendEntries from a newer leader.
        leader2 = self.elect(cluster, max_ticks=ELECTION_TIMEOUT_MAX * 2)
        peer2 = next(i for i in cluster.nodes if i != leader2.id)
        higher2 = leader2.current_term + 1
        leader2.receive(
            AppendEntries(
                term=higher2,
                leader_id=peer2,
                prev_log_index=0,
                prev_log_term=0,
                entries=(),
                leader_commit=0,
            ),
            src=peer2,
        )
        self.assertIs(leader2.state, State.FOLLOWER)
        self.assertEqual(leader2.current_term, higher2)


class TestLogReplication(RaftTestBase):
    def test_log_replication_and_majority_commit(self):
        cluster = self.make_cluster(seed=5)
        leader = self.elect(cluster)
        idx = leader.submit("x=1")
        cluster.tick(HEARTBEAT_TICKS := 60)  # allow commit broadcast
        for node in cluster.nodes.values():
            self.assertEqual(log_tuple(node), log_tuple(leader))
            self.assertEqual(node.commit_index, idx)
            self.assertEqual(node.state_machine, {"x": "1"})

    def test_multiple_commands_apply_in_order(self):
        cluster = self.make_cluster(seed=6)
        leader = self.elect(cluster)
        for i in range(10):
            leader.submit(f"key{i}=v{i}")
        cluster.tick(100)
        expected = {f"key{i}": f"v{i}" for i in range(10)}
        for node in cluster.nodes.values():
            self.assertEqual(node.state_machine, expected)
            self.assertEqual(node.commit_index, leader.last_log_index())

    def test_follower_rejects_inconsistent_append_entries(self):
        cluster = self.make_cluster(seed=8)
        leader = self.elect(cluster)
        follower = next(
            n for n in cluster.nodes.values() if n.id != leader.id
        )
        # Fabricate a divergent uncommitted tail on the follower. The
        # bogus term (999) guarantees an (index, term) mismatch so the
        # leader is forced to repair the log via next_index backoff.
        from raft import LogEntry

        follower.log.append(LogEntry(term=999, command="junk=1"))
        leader.submit("real=1")
        cluster.tick(100)
        # Follower log must have been repaired by next_index backoff.
        self.assertEqual(log_tuple(follower), log_tuple(leader))
        self.assertNotIn("junk", follower.state_machine)


class TestPartitionTolerance(RaftTestBase):
    def test_minority_partition_cannot_elect_or_commit(self):
        cluster = self.make_cluster(seed=9)
        leader = self.elect(cluster)
        minority = {leader.id, (leader.id + 1) % 5}
        majority = set(cluster.nodes) - minority
        cluster.partition(minority, majority)

        stale = leader.submit("stale=1")
        cluster.tick(ELECTION_TIMEOUT_MAX * 3)

        # The isolated leader cannot reach quorum: entry stays uncommitted.
        self.assertLess(leader.commit_index, stale)
        self.assertNotIn("stale", leader.state_machine)
        for i in minority:
            self.assertNotIn("stale", cluster.nodes[i].state_machine)

        # No node in the minority ever became/kept leadership... the old
        # leader may *think* it leads (legal), but cannot commit anything.
        minority_commits = {
            cluster.nodes[i].commit_index for i in minority
        }
        self.assertTrue(all(c < stale for c in minority_commits))

    def test_majority_partition_continues_committing(self):
        cluster = self.make_cluster(seed=10)
        old_leader = self.elect(cluster)
        minority = {old_leader.id, (old_leader.id + 2) % 5}
        majority = set(cluster.nodes) - minority
        cluster.partition(minority, majority)

        new_leader = self.elect(cluster, among=majority,
                                max_ticks=ELECTION_TIMEOUT_MAX * 2)
        self.assertIn(new_leader.id, majority)
        idx = new_leader.submit("alive=1")
        cluster.tick(100)
        self.assertGreaterEqual(new_leader.commit_index, idx)
        for i in majority:
            self.assertEqual(cluster.nodes[i].state_machine, {"alive": "1"})

    def test_partition_heal_truncates_and_converges(self):
        cluster = self.make_cluster(seed=11)
        old_leader = self.elect(cluster)
        old_leader.submit("base=0")
        cluster.tick(100)

        minority = {old_leader.id, (old_leader.id + 1) % 5}
        majority = set(cluster.nodes) - minority
        cluster.partition(minority, majority)

        # Speculative writes in the minority: replicated to <=2 nodes.
        old_leader.submit("spec=bad")
        cluster.tick(200)
        self.assertNotIn(
            "spec", cluster.nodes[old_leader.id].state_machine,
            "minority partitioned leader committed without quorum",
        )

        # Majority elects a new leader and commits real entries.
        new_leader = self.elect(cluster, among=majority,
                                max_ticks=ELECTION_TIMEOUT_MAX * 2)
        new_leader.submit("a=1")
        new_leader.submit("b=2")
        cluster.tick(100)
        for i in majority:
            self.assertEqual(
                cluster.nodes[i].state_machine,
                {"a": "1", "b": "2", "base": "0"},
            )

        # Heal: the minority must step down, truncate "spec=bad", and
        # converge to the majority's log and state machine.
        cluster.heal()
        self.assert_converged(cluster, max_ticks=3000)
        for node in cluster.nodes.values():
            self.assertEqual(
                node.state_machine, {"a": "1", "b": "2", "base": "0"}
            )
            self.assertNotIn(
                "spec=bad",
                [e.command for e in node.log],
                "speculative entry was not truncated",
            )
        self.assertEqual(len(cluster.leaders()), 1)

    def test_stale_leader_cannot_overwrite_committed_entries(self):
        # Safety: a partitioned leader's uncommitted entries never survive.
        cluster = self.make_cluster(seed=12)
        old_leader = self.elect(cluster)
        old_leader.submit("committed=1")
        cluster.tick(100)
        self.assertEqual(old_leader.commit_index, old_leader.last_log_index())
        committed_len = len(old_leader.log)

        minority = {old_leader.id, (old_leader.id + 3) % 5}
        majority = set(cluster.nodes) - minority
        cluster.partition(minority, majority)
        old_leader.submit("evil=1")
        new_leader = self.elect(cluster, among=majority,
                                max_ticks=ELECTION_TIMEOUT_MAX * 2)
        new_leader.submit("good=1")
        cluster.heal()
        self.assert_converged(cluster, max_ticks=3000)

        prefixes = {
            log_tuple(n)[:committed_len] for n in cluster.nodes.values()
        }
        self.assertEqual(len(prefixes), 1,
                         "committed prefix diverged after heal")
        for node in cluster.nodes.values():
            self.assertIn("good=1", [e.command for e in node.log])
            self.assertNotIn("evil=1", [e.command for e in node.log])


class TestAdversarialStress(RaftTestBase):
    def test_randomized_partitions_never_lose_commits(self):
        """Fuzz: random partitions/heals/submits; committed entries and
        state machines must converge once the network heals."""
        rng = random.Random("adversarial:0")
        cluster = self.make_cluster(seed=13)
        ids = list(cluster.nodes)

        committed_submits = []
        for round_ in range(60):
            action = rng.random()
            if action < 0.35:
                # Random 2-way partition.
                rng.shuffle(ids)
                cut = rng.randint(1, len(ids) - 1)
                cluster.heal()
                cluster.partition(set(ids[:cut]), set(ids[cut:]))
            elif action < 0.5:
                cluster.heal()
            else:
                leader = cluster.leader()
                if leader is not None:
                    try:
                        cmd = f"r{round_}={round_}"
                        leader.submit(cmd)
                        committed_submits.append(cmd)
                    except RuntimeError:
                        pass
            cluster.tick(rng.randint(1, 80))

            # Safety invariant under any partition: at most one committed
            # prefix length per index across the whole cluster.
            longest = max(
                (log_tuple(n) for n in cluster.nodes.values()), key=len
            )
            for node in cluster.nodes.values():
                for i, entry in enumerate(node.log[: node.commit_index]):
                    self.assertEqual(
                        (entry.term, entry.command), longest[i],
                        "committed entries diverged",
                    )

        cluster.heal()
        self.assert_converged(cluster, max_ticks=5000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
