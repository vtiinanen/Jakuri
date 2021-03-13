# Jakuri
Distributed Systems project repository

## Prequisities

 * Docker
 * Python

## How to run Jakuri

1. Run Docker containers:
```
docker-compose up
```

2. Start server-coordinator:
```
python server-coordinator.py -i .\arglists\passwords.txt -f shacrack -w 15
```
## Creating arglist for Sha256Crack

1. Run passwordslistchanger-script

```
python passwordslistchanger.py -i .\arglists\Top304Thousand-probable-v2.txt -o .\arglists\passwords.txt -a 1000
```
