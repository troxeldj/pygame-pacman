from collections import deque

from .game_map import GameMap
from .orientation import Orientation


def bfs_next_step(
    start: tuple[int, int], target: tuple[int, int], game_map: GameMap
) -> Orientation | None:
    """Return the orientation of the first step on the shortest path from
    `start` to `target`, or None if they're equal or `target` is unreachable.
    """
    if start == target:
        return None

    parent: dict[tuple[int, int], tuple[tuple[int, int], Orientation]] = {}
    visited = {start}
    queue: deque[tuple[int, int]] = deque([start])

    while queue:
        current = queue.popleft()
        if current == target:
            break

        for orientation in Orientation:
            dx, dy = orientation.delta
            next_cell = (current[0] + dx, current[1] + dy)
            if next_cell in visited or not game_map.is_walkable(*next_cell):
                continue
            visited.add(next_cell)
            parent[next_cell] = (current, orientation)
            queue.append(next_cell)

    if target not in parent:
        return None

    step = target
    while parent[step][0] != start:
        step = parent[step][0]
    return parent[step][1]
