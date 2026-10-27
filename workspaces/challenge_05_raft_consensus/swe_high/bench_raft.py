"""Performance harness for the Raft simulation (profilable by devin-bench).

Runs a sustained workload: repeated client submits interleaved with
partition/heal cycles, then forces full convergence and reports metrics.
Top-level code so `runpy.run_path` executes it directly.
"""

import random
import time

from raft import Cluster

ROUNDS = 400
SUBMITS_PER_ROUND = 5

rng = random.Random("bench:0")
cluster = Cluster(size=5, seed=99)
leader = cluster.wait_for_leader()

t0 = time.perf_counter()
submitted = committed_cmds = 0
for r in range(ROUNDS):
    for _ in range(SUBMITS_PER_ROUND):
        node = cluster.leader()
        if node is not None:
            node.submit(f"k{r}_{submitted}=v")
            submitted += 1
    if r % 20 == 19:
        ids = list(cluster.nodes)
        rng.shuffle(ids)
        cut = rng.randint(1, 4)
        cluster.heal()
        cluster.partition(set(ids[:cut]), set(ids[cut:]))
    elif r % 20 == 9:
        cluster.heal()
    cluster.tick(rng.randint(5, 40))

cluster.heal()
# Drive to full convergence.
for _ in range(6000):
    cluster.tick()
    logs = {tuple(e.command for e in n.log) for n in cluster.nodes.values()}
    commits = {n.commit_index for n in cluster.nodes.values()}
    if len(logs) == 1 and len(commits) == 1:
        break

elapsed = time.perf_counter() - t0
msgs = cluster.network.delivered_count
drops = cluster.network.dropped_count
final_term = max(n.current_term for n in cluster.nodes.values())
commit = cluster.nodes[0].commit_index
applied = len(cluster.nodes[0].state_machine)

print(f"[BENCH] submits={submitted} applied_keys={applied} "
      f"committed_index={commit} final_term={final_term}")
print(f"[BENCH] messages_delivered={msgs} dropped={drops} "
      f"simulated_ticks={cluster.time}")
print(f"[BENCH] wall_time={elapsed:.4f}s  "
      f"msgs/s={msgs / max(elapsed, 1e-9):,.0f}")
