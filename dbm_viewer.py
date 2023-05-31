import argparse
import dbm
from pathlib import Path

from rich.console import Console
from rich.table import Table

parser = argparse.ArgumentParser()
parser.add_argument("path")
args = parser.parse_args()

path = Path(args.path)

table = Table(title=str(path))
table.add_column("Key")
table.add_column("Value")

with dbm.open(path, "r") as db:
    k = db.firstkey()
    while k is not None:
        table.add_row(k.decode("utf-8"), db[k].decode("utf-8"))
        k = db.nextkey(k)

console = Console()
console.print(table)
