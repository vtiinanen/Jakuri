# Jakuri
Distributed Systems project repository

## Prequisities

 * Docker
 * Python 3

## How to run Jakuri

1. Run Docker containers:
```
docker-compose up
```

2. Start server-coordinator:
```bash
python server-coordinator.py -f shacrackprod -H 87e93406a19d11166fd4aff9addf299aad2221cbd45febc596a527b65269b78f -l 5 -c abcdefghijklmnopqrstuvwxyz
```
Different functions that can be run are:
* shacrack
* shacrackprod
