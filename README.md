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
python server-coordinator.py -f shacrackprod -H 87e93406a19d11166fd4aff9addf299aad2221cbd45febc596a527b65269b78f -l 5 -c abcdefghijklmnopqrstuvwxyz -w 1
```
Different functions that can be run are:
* shacrack
* shacrackprod
* fibonacci
* sleep

## Creating arglist for shacrack

1. Run passwordslistchanger-script

```bash
python passwordslistchanger.py -i .\arglists\Top304Thousand-probable-v2.txt -o .\arglists\passwords.txt -a 1000
```
