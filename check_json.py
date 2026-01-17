from pathlib import Path
import json

file_path = Path("./site/assets/kittens.json")

with open(file=file_path) as f:
    data = json.load(f)

print(type(data))

print(len(data))
