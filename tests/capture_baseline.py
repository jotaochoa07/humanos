import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(BASE_DIR, "tests")
BASELINES_DIR = os.path.join(TESTS_DIR, "baselines")

os.makedirs(BASELINES_DIR, exist_ok=True)

def capture_ep0001_baseline():
    jan_koum_dir = os.path.join(BASE_DIR, "personajes", "Jan_Koum", "EP0001_Jan_Koum")
    script_dir = os.path.join(jan_koum_dir, "02_SCRIPT")
    
    baseline = {
        "episode": "Jan_Koum_EP0001",
        "pipeline_state": None,
        "scripts_json": None,
        "script_short_md": None
    }
    
    state_file = os.path.join(jan_koum_dir, "pipeline_state.json")
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            baseline["pipeline_state"] = json.load(f)
            
    scripts_json_file = os.path.join(script_dir, "scripts.json")
    if os.path.exists(scripts_json_file):
        with open(scripts_json_file, "r", encoding="utf-8") as f:
            baseline["scripts_json"] = json.load(f)
            
    script_md_file = os.path.join(script_dir, "script_short.md")
    if os.path.exists(script_md_file):
        with open(script_md_file, "r", encoding="utf-8") as f:
            baseline["script_short_md"] = f.read()

    baseline_path = os.path.join(BASELINES_DIR, "ep0001_short_baseline.json")
    with open(baseline_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)
        
    print(f"[Baseline Captured] Saved snapshot to {baseline_path}")

if __name__ == "__main__":
    capture_ep0001_baseline()
