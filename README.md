# Jakuri
Distributed Systems project repository

## Prequisities

 * Docker
 * Python

## How to run

1. Run Docker containers:
```
docker-compose up
```

2. Start server-coordinator:
```
python server-coordinator.py -i ./arglists/passwords.txt -f shacrack -w 15
```
