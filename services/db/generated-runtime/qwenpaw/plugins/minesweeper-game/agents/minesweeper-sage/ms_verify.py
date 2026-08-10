import random

N = 9
MINES = 10
TRIALS = 3_000_000
random.seed(42)

def neighbors(r, c):
    out = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                out.append((nr, nc))
    return out

# 0-based: (0,0),(0,1),(0,2) == 第一行前三个格子 (翻开为 1 1 1)
targets = [(0, 0), (0, 1), (0, 2)]
counts = {(1, 0): 0, (1, 1): 0, (1, 2): 0, (0, 3): 0, (1, 3): 0}
total = 0

for _ in range(TRIALS):
    cells = [(r, c) for r in range(N) for c in range(N)]
    mines = set(random.sample(cells, MINES))
    if any((r, c) in mines for (r, c) in targets):
        continue
    ok = True
    for (r, c) in targets:
        if sum(1 for (nr, nc) in neighbors(r, c) if (nr, nc) in mines) != 1:
            ok = False
            break
    if not ok:
        continue
    total += 1
    for (r, c) in counts:
        if (r, c) in mines:
            counts[(r, c)] += 1

print("samples:", total)
for k, v in counts.items():
    print(k, "=>", v / total)
