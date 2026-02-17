import json
from datetime import datetime

with open("remi-scholar.json", "r") as f:
    data = json.load(f)

data["last_updated"] = datetime.today().strftime("%Y-%m-%d")

with open("remi-scholar.json", "w") as f:
    json.dump(data, f, indent=4)

print("REMI Scholar JSON updated successfully.")
