def find_all_paths(graph, start, end):
    def dfs(current, path, visited):
        path.append(current)
        visited.add(current)
        if current == end:
            paths.append(path.copy())
        else:
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    dfs(neighbor, path, visited)
        path.pop()
        visited.remove(current)
    paths = []
    dfs(start, [], set())
    for i in range(len(paths)):
        paths[i] = paths[i][:-1]
    return paths