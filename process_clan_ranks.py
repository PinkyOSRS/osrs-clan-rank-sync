import os
import json
import glob

def process_clan_ranks():
    """
    Find the latest clan rank file in the uploads directory and process it.
    Generate a simplified JSON file for the Discord bot that includes rank and joinedDate.
    """
    # Ensure uploads directory exists
    os.makedirs("uploads", exist_ok=True)
    
    # Find all JSON files in the uploads directory
    json_files = glob.glob("uploads/*.json")
    if not json_files:
        print("No clan rank files found in the uploads directory.")
        return
    
    # Sort files by modification time (newest first)
    latest_file = max(json_files, key=os.path.getmtime)
    print(f"Processing latest file: {latest_file}")
    
    try:
        # Read the latest file
        with open(latest_file, "r") as f:
            data = json.load(f)
            clanmates = data.get("clanMemberMaps", [])
        
        # Extract the clan ranks and joined dates
        clan_dict = {
            entry["rsn"]: {
                "rank": entry["rank"],
                "joinedDate": entry["joinedDate"]
            }
            for entry in clanmates
            if all(k in entry for k in ("rsn", "rank", "joinedDate"))
        }

        # Sort by RSN alphabetically (optional)
        clan_dict = dict(sorted(clan_dict.items(), key=lambda item: item[0]))
        
        # Write the processed output
        with open("clan_ranks_for_bot.json", "w") as f:
            json.dump(clan_dict, f, indent=2)
        
        print(f"Successfully processed {len(clan_dict)} clan members.")
        print("Output saved to clan_ranks_for_bot.json")
        
    except Exception as e:
        print(f"Error processing file {latest_file}: {str(e)}")

if __name__ == "__main__":
    process_clan_ranks()
