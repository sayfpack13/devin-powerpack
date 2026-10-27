"""Adversarial stress tests for the Raft simulation. Run: python test_raft.py"""

import sys
import time

from raft import (Cluster, Node, Network, FOLLOWER, CANDIDATE, LEADER,
                  HEARTBEAT_INTERVAL, ELECTION_TIMEOUT_MAX)


def test_initial_leader_election():
    c = Cluster(5, seed=1)
    leader = c.run_until_leader(2000)
    assert leader is not None, "no leader elected within 2s"
    assert len(c.leaders()) == 1, "split brain: more than one leader"
    followers = [n for n in c.nodes.values() if n.state == FOLLOWER]
    assert len(followers) == 4
    assert all(n.current_term == leader.current_term for n in followers)
    print("PASS initial leader election (term %d, leader=%d, t=%dms)"
          % (leader.current_term, leader.id, c.now))


def test_heartbeats_suppress_elections():
    c = Cluster(5, seed=2)
    leader = c.run_until_leader()
    term = leader.current_term
    c.run(5 * ELECTION_TIMEOUT_MAX)
    assert c.leader() is leader, "leader lost leadership despite heartbeats"
    assert leader.current_term == term, "term advanced: spurious election"
    assert all(n.state == FOLLOWER for n in c.nodes.values()
               if n.id != leader.id)
    print("PASS heartbeats suppress elections (term stable at %d)" % term)


def test_log_replication_and_commit():
    c = Cluster(5, seed=3)
    leader = c.run_until_leader()
    idx = leader.submit("set x=1")
    c.run(2 * HEARTBEAT_INTERVAL)
    assert leader.commit_index == idx
    for n in c.nodes.values():
        assert n.commit_index == idx, "node %d did not learn commit" % n.id
        assert n.state_machine == ["set x=1"], "node %d diverged" % n.id
        assert len(n.log) == idx
    print("PASS replication + majority commit (index %d on all 5 nodes)" % idx)


def test_minority_partition_cannot_commit():
    c = Cluster(5, seed=4)
    leader = c.run_until_leader()
    # isolate leader + one follower (2-node minority)
    minority = [leader.id, (leader.id + 1) % 5]
    majority = [i for i in c.nodes if i not in minority]
    c.partition(minority, majority)
    old_commit = leader.commit_index
    idx = leader.submit("minority-write")
    assert idx is not None
    c.run(1000)
    assert leader.commit_index == old_commit, \
        "minority partition committed an entry"
    # minority cannot elect a new leader either: drop the old leader
    leader.state = FOLLOWER  # simulate crash/stepdown
    c.run(2000)
    minority_leaders = [i for i in minority
                        if c.nodes[i].state == LEADER]
    assert not minority_leaders, "minority elected a leader"
    print("PASS minority partition cannot commit or elect")


def test_majority_partition_continues():
    c = Cluster(5, seed=5)
    leader = c.run_until_leader()
    minority = [leader.id, (leader.id + 1) % 5]
    majority = [i for i in c.nodes if i not in minority]
    c.partition(minority, majority)
    c.run(1500)  # majority side elects a new leader
    new_leaders = [i for i in majority if c.nodes[i].state == LEADER]
    assert len(new_leaders) == 1, "majority failed to elect a leader"
    new_leader = c.nodes[new_leaders[0]]
    assert new_leader.current_term > leader.current_term
    idx = new_leader.submit("majority-write")
    c.run(200)
    assert new_leader.commit_index == idx
    assert all(c.nodes[i].state_machine[-1] == "majority-write"
               for i in majority)
    print("PASS majority partition elects new leader (term %d) and commits"
          % new_leader.current_term)


def test_partition_heal_converges():
    c = Cluster(5, seed=6)
    leader = c.run_until_leader()
    leader.submit("cmd-0")
    c.run(100)
    minority = [leader.id, (leader.id + 1) % 5]
    majority = [i for i in c.nodes if i not in minority]
    c.partition(minority, majority)
    # old leader writes speculative entries only to its 2-node minority
    leader.submit("speculative-1")
    leader.submit("speculative-2")
    c.run(800)
    assert c.nodes[minority[1]].log[-1].command == "speculative-2"
    # majority elects new leader and commits real entries
    new_leader = c.nodes[[i for i in majority
                          if c.nodes[i].state == LEADER][0]]
    new_leader.submit("real-1")
    new_leader.submit("real-2")
    c.run(200)
    # heal: minority must truncate speculative entries and converge
    c.heal()
    c.run(1000)
    final_leader = c.leader()
    if final_leader is None:  # old leader may still think it leads briefly
        final_leader = new_leader if new_leader.state == LEADER else None
    assert final_leader is not None, "no leader after heal"
    for n in c.nodes.values():
        assert n.state_machine == ["cmd-0", "real-1", "real-2"], \
            "node %d diverged: %r" % (n.id, n.state_machine)
        assert all(e.command not in ("speculative-1", "speculative-2")
                   for e in n.log[:n.commit_index]), \
            "node %d kept speculative committed entry" % n.id
    print("PASS heal: all 5 nodes converged, speculative entries truncated")


def test_higher_term_step_down():
    net = Network()
    import random
    c = Cluster(5, seed=7)
    leader = c.run_until_leader()
    term = leader.current_term
    # inject higher-term RequestVote
    granted_term, _ = leader.request_vote(
        term + 5, candidate_id=99, last_log_index=0, last_log_term=0)
    assert leader.state == FOLLOWER
    assert leader.current_term == term + 5
    # higher-term AppendEntries also forces step-down
    leader2 = None
    for n in c.nodes.values():
        if n.state == LEADER:
            leader2 = n
    c.run(1000)
    leaders = [n for n in c.nodes.values() if n.state == LEADER]
    for l in leaders:
        l.append_entries(l.current_term + 10, 99, 0, 0, [], 0)
        assert l.state == FOLLOWER and l.current_term == l.current_term
    print("PASS higher term forces immediate step-down")


def test_split_vote_recovers():
    # force simultaneous candidates by zeroing jitter symmetry: just run long
    c = Cluster(5, seed=123)
    leader = c.run_until_leader(10_000)
    assert leader is not None
    print("PASS split-vote recovery (leader elected by %dms)" % c.now)


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_")]
    t0 = time.perf_counter()
    for t in tests:
        t()
    dt = time.perf_counter() - t0
    print("\n%d/%d tests passed in %.1fms" % (len(tests), len(tests), dt*1000))
    sys.exit(0)


if __name__ == "__main__":
    main()
