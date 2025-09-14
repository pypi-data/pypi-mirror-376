# graphs_mcsteestu: Dijkstra's Shortest Path Algorithm in Python

A Python library for running Dijkstra's shortest path algorithm on weighted graphs with non-negative weights. This project uses a priority queue algorithm to implement Dijkstra's shortest path algorithm.   


## How to install the graphs_mcsteestu library
```
pip3 install graphs_mcsteestu
```

## How to use the graphs_mcsteestu library

### Import the package into your Python file

```
from graphs_mcsteestu import sp
```

## Example Python file and library usage

### Test File test.py :
```
from graphs_mcsteestu import sp
import sys

if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        print(f'Use: {sys.argv[0]} graph_file')
        sys.exit(1)

    graph = {}
    with open(sys.argv[1], 'rt') as f:
        f.readline() # skip first line
        for line in f:
            line = line.strip()
            s, d, w = line.split()
            s = int(s)
            d = int(d)
            w = int(w)
            if s not in graph:
                graph[s] = {}
            graph[s][d] = w
    
    print("Dijkstra's Shortest Path Algorithm")
    s = 0
    dist, path = sp.dijkstra(graph, s)
    print(f'Shortest distances from {s}:')
    print(dist)
    for d in path: 
        print(f'spf to {d}: {path[d]}')
```

### Command:
```
python3 test.py GraphNodes.txt
```


## Credits
* Dr. Mota for providing the code for implementing Dijkstra's algorithm.
* Kevin O'Connor, Tim Peters, and Raymond Hettinger for providing the code implementing the heap queue algorithm in python.

## License
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)