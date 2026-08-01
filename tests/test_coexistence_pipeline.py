import os
import json
import unittest
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from borges import BorgesAgent
from talese import TaleseAgent
from gabo import GaboAgent
from moore import MooreAgent
from mark import MarkAgent

class DummyClient:
    """Mock OpenRouterClient for deterministic testing."""
    def complete_json(self, prompt, system_prompt="", model=None):
        if "Gay Talese" in system_prompt:
            return {
                "approved": True,
                "structural_score": 9,
                "editorial_feedback": "Estructura por actos sólida y fuertemente causal.",
                "rejection_reasons": [],
                "socratic_questions": ["¿El conflicto del Acto I justifica la inversión del Acto II?"]
            }
        if "BORGES" in system_prompt:
            return {
                "character_name": "Ferruccio Lamborghini",
                "central_thesis": "La revancha técnica frente a la arrogancia industrial.",
                "main_conflict": "El choque existencial entre el fabricante de tractores y Enzo Ferrari.",
                "target_total_duration_sec": 540,
                "beat_sheet": [
                    { "id": "act_1", "title": "Acto I: La afrenta de Enzo", "estimated_duration_sec": 90, "causality_type": "BUT", "status": "draft" },
                    { "id": "act_2", "title": "Acto II: El taller clandestino", "estimated_duration_sec": 90, "causality_type": "THEREFORE", "status": "draft" },
                    { "id": "act_3", "title": "Acto III: El 350 GTV", "estimated_duration_sec": 100, "causality_type": "BUT", "status": "draft" },
                    { "id": "act_4", "title": "Acto IV: Ruptura en Ginebra", "estimated_duration_sec": 110, "causality_type": "THEREFORE", "status": "draft" },
                    { "id": "act_5", "title": "Acto V: El mito del Toro", "estimated_duration_sec": 90, "causality_type": "BUT", "status": "draft" }
                ],
                "talese_open_questions": ["¿Por qué el embrague del tractor era idéntico al del Ferrari?"]
            }
        if "GABO" in system_prompt:
            return {
                "act_id": "act_1",
                "title": "Acto I: La afrenta de Enzo",
                "script_text": "Ferruccio Lamborghini conducía su Ferrari 250 GT con furia... [B-ROLL: Ferruccio conduciendo en Maranello]",
                "word_count": 180,
                "estimated_duration_sec": 90,
                "status": "draft"
            }
        return {}


    def complete_text(self, prompt, system_prompt, model=None):
        return "Contenido de texto de prueba."

class TestCoexistencePipeline(unittest.TestCase):
    
    def test_01_baseline_short_mode_integrity(self):
        """Verifica que el baseline guardado de EP0001 (Jan Koum) exista y mantenga integridad."""
        baseline_file = os.path.join(BASE_DIR, "tests", "baselines", "ep0001_short_baseline.json")
        self.assertTrue(os.path.exists(baseline_file), "El archivo baseline de EP0001 debe existir.")
        
        with open(baseline_file, "r", encoding="utf-8") as f:
            baseline = json.load(f)
            
        self.assertEqual(baseline.get("episode"), "Jan_Koum_EP0001")
        self.assertIsNotNone(baseline.get("pipeline_state"))
        self.assertIn(baseline["pipeline_state"].get("status"), ["script_pending_review", "storyboard_done"])


    def test_02_borges_blueprint_decoupled_execution(self):
        """Verifica que Borges genere el Narrative Blueprint a partir de un dossier existente sin re-investigar."""
        client = DummyClient()
        borges = BorgesAgent(client)
        
        dossier_sample = "# Dossier Editorial: Ferruccio Lamborghini\n\n## 1. Editorial Thesis\nLa revancha mecánica."
        blueprint = borges.build_narrative_blueprint("Ferruccio Lamborghini", "La revancha industrial", dossier_sample)
        
        self.assertIn("beat_sheet", blueprint)
        self.assertEqual(len(blueprint["beat_sheet"]), 5)
        self.assertEqual(blueprint["character_name"], "Ferruccio Lamborghini")

    def test_03_talese_gate1_audit_and_rejection_flow(self):
        """Verifica que Talese Gate 1 apruebe blueprints válidos y rechace estructuras débiles."""
        talese = TaleseAgent(base_dir=BASE_DIR)
        talese.client = DummyClient()
        
        valid_bp = {
            "character_name": "Ferruccio Lamborghini",
            "target_total_duration_sec": 480,
            "beat_sheet": [
                { "id": f"act_{i}", "causality_type": "BUT", "estimated_duration_sec": 90 } for i in range(1, 6)
            ]
        }
        res_valid = talese.audit_beat_sheet_gate1(valid_bp)
        self.assertTrue(res_valid.get("approved"))
        
        invalid_bp = {
            "character_name": "Ferruccio Lamborghini",
            "target_total_duration_sec": 200, # Demasiado corto (<420s)
            "beat_sheet": [ { "id": "act_1", "causality_type": "AND_THEN" } ] # Solo 1 acto y causalidad débil
        }
        res_invalid = talese.audit_beat_sheet_gate1(invalid_bp)
        self.assertFalse(res_invalid.get("approved"))
        self.assertGreater(len(res_invalid.get("rejection_reasons", [])), 0)

    def test_04_gabo_act_by_act_context_injection(self):
        """Verifica que Gabo redacte actos inyectando la tesis central como contexto inmutable."""
        client = DummyClient()
        gabo = GaboAgent(client)
        
        blueprint = {
            "central_thesis": "Tesis Inmutable de Prueba",
            "main_conflict": "Conflicto Inmutable de Prueba",
            "beat_sheet": [
                { "id": "act_1", "title": "Acto I", "estimated_duration_sec": 90 }
            ]
        }
        
        act_result = gabo.execute_narrative_by_act("Ferruccio Lamborghini", blueprint, 0)
        self.assertEqual(act_result.get("act_id"), "act_1")
        self.assertIn("script_text", act_result)

    def test_05_moore_and_mark_dual_packaging(self):
        """Verifica que Moore mapee assets por acto y Mark genere el empaquetado dual con 3 shorts derivados."""
        client = DummyClient()
        moore = MooreAgent(client)
        mark = MarkAgent(base_dir=BASE_DIR)
        
        beat_sheet = [{ "id": "act_1", "title": "Acto I" }, { "id": "act_2", "title": "Acto II" }]
        manifest_assets = [{ "asset_id": "001", "name": "Foto Lamborghini" }]
        
        act_assets = moore.map_assets_by_act("Ferruccio Lamborghini", beat_sheet, manifest_assets)
        self.assertIn("act_1", act_assets)
        
        derived_shorts = [
            { "short_id": "short_01", "episodio_padre_id": "EP_LAMBORGHINI_DOC", "acto_origen_id": "act_1", "is_derived_short": True }
        ]
        
        ferruccio_dir = os.path.join(BASE_DIR, "personajes", "Ferruccio_Lamborghini", "EP0004_Ferruccio_Lamborghini")
        os.makedirs(os.path.join(ferruccio_dir, "11_DIST"), exist_ok=True)
        
        dual_pack = mark.package_dual_distribution(ferruccio_dir, "Ferruccio Lamborghini", {"central_thesis": "La revancha técnica"}, derived_shorts)
        
        self.assertTrue(dual_pack.get("is_documentary_pilot"))
        self.assertEqual(dual_pack.get("character_name"), "Ferruccio Lamborghini")
        self.assertEqual(len(dual_pack.get("derived_shorts", [])), 1)
        self.assertTrue(os.path.exists(os.path.join(ferruccio_dir, "11_DIST", "distribution_dual_pack.json")))


if __name__ == "__main__":
    unittest.main()
