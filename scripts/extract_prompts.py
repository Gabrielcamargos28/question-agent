import json
import os
import glob

def extract_prompts(directory):
    files = glob.glob(os.path.join(directory, "*.json*"))
    all_prompts = []
    
    for file_path in sorted(files):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.endswith(".jsonl"):
                    for line in f:
                        try:
                            data = json.loads(line)
                            if data.get("type") == "user":
                                content = data.get("content", "")
                                if isinstance(content, list):
                                    text = ""
                                    for part in content:
                                        if isinstance(part, dict) and "text" in part:
                                            text += part["text"]
                                        elif isinstance(part, str):
                                            text += part
                                    all_prompts.append(text)
                                elif isinstance(content, str):
                                    all_prompts.append(content)
                        except json.JSONDecodeError:
                            continue
                else:
                    data = json.load(f)
                    # For standard .json files
                    entries = []
                    if isinstance(data, list):
                        entries = data
                    elif isinstance(data, dict):
                        if "history" in data:
                            entries = data["history"]
                        elif "messages" in data:
                            entries = data["messages"]
                        else:
                            # Maybe it's a single session object with entries?
                            pass
                    
                    for entry in entries:
                        if entry.get("role") == "user" or entry.get("type") == "user":
                            content = entry.get("content", "")
                            if isinstance(content, list):
                                text = ""
                                for part in content:
                                    if isinstance(part, dict) and "text" in part:
                                        text += part["text"]
                                    elif isinstance(part, str):
                                        text += part
                                all_prompts.append(text)
                            elif isinstance(content, str):
                                all_prompts.append(content)

        except Exception as e:
            # print(f"Error reading {file_path}: {e}")
            pass
            
    return all_prompts

chats_dir = r"C:\Users\gabrielcamargos\.gemini\tmp\agente-questoes\chats"
prompts = extract_prompts(chats_dir)

# Remove duplicates and empty prompts, maintaining order
seen = set()
unique_prompts = []
for p in prompts:
    if p and p.strip() and p not in seen:
        unique_prompts.append(p.strip())
        seen.add(p)

for i, p in enumerate(unique_prompts):
    # Truncate very long prompts for display
    display_p = p if len(p) < 500 else p[:497] + "..."
    print(f"{i+1}. {display_p}\n")
