"""
Slicer cascade and interaction logic for VISA Slicer Demo
"""
import json
from pathlib import Path

# Load config
CONFIG_FILE = Path(__file__).parent.parent / "config.json"
with open(CONFIG_FILE) as f:
    config = json.load(f)

WORKSPACE_ID = config["fabric"]["workspaceId"]
REPORT_ID = config["fabric"]["reportId"]

class SlicerCascade:
    """Manage cascading slicer interactions"""
    
    def __init__(self):
        self.slicer_state = {
            "Slicer_Year": None,
            "Slicer_Region": None,
            "Slicer_Product": None,
            "Slicer_Category": None
        }
    
    def set_slicer(self, slicer_name: str, value: str) -> None:
        """Set a slicer value and trigger cascade"""
        if slicer_name in self.slicer_state:
            self.slicer_state[slicer_name] = value
            self._cascade()
    
    def _cascade(self) -> None:
        """Apply cascade logic when a slicer changes"""
        # TODO: Implement cascade logic
        # Example: When Year changes, update Region options
        pass
    
    def get_state(self) -> dict:
        """Get current slicer state"""
        return self.slicer_state

if __name__ == "__main__":
    cascade = SlicerCascade()
    cascade.set_slicer("Slicer_Year", "2020")
    print(cascade.get_state())
