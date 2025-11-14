import os
import json
from datetime import datetime

# Full path to memory file
MEMORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "memory",
    "agent_memory.json"
)


class AgentMemory:
    def __init__(self):
        # Ensure folder exists
        memory_dir = os.path.dirname(MEMORY_FILE)
        os.makedirs(memory_dir, exist_ok=True)

        # Ensure file exists
        if not os.path.exists(MEMORY_FILE):
            self._initialize_memory()

    # --------------------------------------------
    # Create the memory file with empty structure
    # --------------------------------------------
    def _initialize_memory(self):
        initial_data = {
            "history": [],
            "runs": []
        }
        with open(MEMORY_FILE, "w") as f:
            json.dump(initial_data, f, indent=4)

    # --------------------------------------------
    # Read memory safely
    # --------------------------------------------
    def read_memory(self):
        if not os.path.exists(MEMORY_FILE):
            self._initialize_memory()

        with open(MEMORY_FILE, "r") as f:
            content = f.read().strip()

            # If file is accidentally empty, reinitialize
            if content == "":
                self._initialize_memory()
                return self.read_memory()

            return json.loads(content)

    # --------------------------------------------
    # Write memory safely
    # --------------------------------------------
    def _write_memory(self, data):
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=4)

    # --------------------------------------------
    # Save chat message
    # --------------------------------------------
    def save_message(self, role: str, content: str):
        data = self.read_memory()

        data["history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })

        self._write_memory(data)

    # --------------------------------------------
    # Save audit run
    # --------------------------------------------
    def save_run(self, agent: str, summary: str):
        data = self.read_memory()

        data["runs"].append({
            "agent": agent,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        })

        self._write_memory(data)

    # --------------------------------------------
    # Convert chat history to text
    # --------------------------------------------
    def get_history_as_text(self):
        data = self.read_memory()

        lines = []
        for entry in data["history"]:
            role = entry["role"].capitalize()
            content = entry["content"]
            lines.append(f"{role}: {content}")

        return "\n".join(lines)
