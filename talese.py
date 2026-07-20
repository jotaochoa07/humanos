import os
import sys
import json
import argparse
from datetime import datetime

class TaleseAgent:
    def __init__(self, base_dir: str = "C:/Users/Jota Ochoa/Antigravity/02_Projects/humanos"):
        self.base_dir = base_dir
        self.learnings_file = os.path.join(base_dir, "_LAB", "creator_learnings.json")

    def run_immediate_retro(self, episode_path: str) -> dict:
        """
        Retro Editorial Inmediata:
        Compara el borrador original de Gabo (script_short_original.md)
        contra la versión editada por Jota (script_short.md).
        """
        script_dir = os.path.join(episode_path, "02_SCRIPT")
        orig_file = os.path.join(script_dir, "script_short_original.md")
        final_file = os.path.join(script_dir, "script_short.md")

        orig_text = ""
        final_text = ""

        if os.path.exists(orig_file):
            with open(orig_file, "r", encoding="utf-8") as f:
                orig_text = f.read()

        if os.path.exists(final_file):
            with open(final_file, "r", encoding="utf-8") as f:
                final_text = f.read()

        episode_name = os.path.basename(os.path.normpath(episode_path))

        report = {
            "episode": episode_name,
            "timestamp": datetime.now().isoformat(),
            "mode": "immediate",
            "has_original_draft": bool(orig_text),
            "original_word_count": len(orig_text.split()) if orig_text else 0,
            "final_word_count": len(final_text.split()) if final_text else 0,
            "summary": f"Retro inmediata registrada para {episode_name}. Delta de edición: {len(orig_text.split())} -> {len(final_text.split())} palabras."
        }

        # Guardar Episode Changelog
        changelog_file = os.path.join(episode_path, "EPISODE_CHANGELOG.json")
        with open(changelog_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"[Talese] Retro Inmediata completada para {episode_name}.")
        return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Talese Editorial Learning Engine")
    parser.add_argument("--episode-path", type=str, required=True, help="Path to episode folder")
    parser.add_argument("--mode", type=str, default="immediate", choices=["immediate", "performance"])
    args = parser.parse_args()

    talese = TaleseAgent()
    if args.mode == "immediate":
        talese.run_immediate_retro(args.episode_path)
