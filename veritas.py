import json
import datetime
from openrouter_client import OpenRouterClient

class VeritasAgent:
    def __init__(self, client: OpenRouterClient):
        self.client = client

    def execute_verification(self, character_name: str, claims_data: dict, research_data: dict, sources_data: dict) -> tuple:
        """
        Ejecuta la verificación de Veritas a través de LLM.
        Devuelve (fact_check_json_dict, approved_claims_json_dict, logs_str).
        """
        print(f"[Veritas] Iniciando fact checking para: {character_name}...")

        system_prompt = (
            "Eres Veritas, el auditor de confianza, fact checker y quality gate del ecosistema Hermoso.\n"
            "Tu único trabajo es auditar hechos, comprobar evidencia, detectar contradicciones y calificar el nivel de confianza.\n"
            "Prefieres declarar incertidumbre con 'No sabemos todavía' antes que asumir falsas certezas.\n"
            "Debes responder estrictamente en formato JSON utilizando el esquema solicitado."
        )

        verification_prompt = f"""
        Audita el siguiente conjunto de afirmaciones (claims) del personaje: {character_name}.
        
        REGLAS DE CONCISIÓN (OBLIGATORIO):
        - Sé extremadamente breve y conciso en las notas y descripciones de las fuentes. No repitas textos extensos.
        - Limita las fuentes listadas a máximo 2 por claim.
        
        Afirmaciones a evaluar (claims):
        {json.dumps(claims_data.get('claims', []), ensure_ascii=False, indent=2)}

        Investigación previa:
        {json.dumps(research_data, ensure_ascii=False, indent=2)}

        Fuentes catalogadas:
        {json.dumps(sources_data.get('sources', []), ensure_ascii=False, indent=2)}

        Evalúa minuciosamente cada claim.
        Reglas de clasificación de Claims:
        - VERIFIED: Existe evidencia sólida.
        - PARTIAL: Evidencia razonable pero incompleta.
        - UNVERIFIED: No existe evidencia suficiente.
        - REJECTED: La evidencia contradice la afirmación.

        Sistema de evaluación (puntuación del 1 al 10 en cada criterio):
        - source_authority (¿Es confiable?)
        - source_independence (¿Son fuentes independientes o copias de la misma?)
        - primary_source_proximity (¿Qué tan cerca de la fuente original está?)
        - consistency (¿Las fuentes coinciden?)
        - contradiction_risk (¿Existen discrepancias o señales de alerta?)

        Score de confianza final (confidence_score) por claim:
        - 90-100: Muy alta confianza
        - 80-89: Alta confianza
        - 70-79: Moderada
        - 60-69: Débil
        - 0-59: No confiable

        Calcula también un overall_confidence_score global (de 0 a 100) para todo el episodio.
        Si overall_confidence_score < 80, el status global debe ser 'NEEDS_REVIEW' o 'REJECTED'. Si es >= 80, es 'APPROVED'.

        Responde con un JSON que tenga EXACTAMENTE esta estructura:
        {{
          "fact_check": {{
            "project": "HUMANOS",
            "episode_id": "EP0001",
            "subject": "{character_name}",
            "checked_at": "{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "overall_confidence_score": 85,
            "status": "APPROVED", // APPROVED | NEEDS_REVIEW | REJECTED
            "format_audit_reports": {{
              "shorts": {{
                "confidence_score": 85,
                "status": "APPROVED",
                "notes": "Auditoría específica para formato vertical corto"
              }},
              "long_form": {{
                "confidence_score": 85,
                "status": "APPROVED",
                "notes": "Auditoría específica para formato largo"
              }},
              "newsletter": {{
                "confidence_score": 85,
                "status": "APPROVED",
                "notes": "Auditoría específica para newsletter editorial"
              }},
              "twitter": {{
                "confidence_score": 85,
                "status": "APPROVED",
                "notes": "Auditoría específica para hilo de X/Twitter"
              }}
            }},
            "claims_summary": {{
              "total": 1,
              "verified": 1,
              "partial": 0,
              "unverified": 0,
              "rejected": 0
            }},
            "claims": [
              {{
                "claim_id": "C001",
                "claim": "WhatsApp fue adquirida por Facebook por 19 mil millones de dólares.",
                "importance": 10,
                "status": "VERIFIED",
                "applicable_formats": ["shorts", "long_form", "newsletter", "twitter"],
                "confidence_score": 95,
                "source_authority": 9,
                "source_independence": 9,
                "primary_source_proximity": 10,
                "consistency": 10,
                "contradiction_risk": 1,
                "sources": [
                  {{
                    "title": "SEC Filing Facebook",
                    "url": "https://www.sec.gov/Archives/edgar/data/1326801/000132680114000045/fb-9302014x10q.htm",
                    "type": "official",
                    "tier": "A",
                    "notes": "Reporte financiero oficial a la SEC."
                  }}
                ],
                "notes": "Confirmado por reguladores financieros.",
                "recommendation": "Se puede usar directamente."
              }}
            ],
            "risks": [],
            "missing_evidence": [],
            "recommended_next_action": "Aprobar para producción de guión."
          }},
          "approved_claims_summary": {{
            "project": "HUMANOS",
            "episode_id": "EP0001",
            "subject": "{character_name}",
            "approved_claims": [
              {{
                "claim_id": "C001",
                "claim": "WhatsApp fue adquirida por Facebook por 19 mil millones de dólares.",
                "status": "VERIFIED",
                "applicable_formats": ["shorts", "long_form", "newsletter", "twitter"],
                "confidence_score": 95,
                "usage_guidance": "Can be used directly" // Can be used directly | Use carefully | Mention uncertainty
              }}
            ],
            "rejected_or_blocked_claims": []
          }}
        }}
        """

        output = self.client.complete_json(verification_prompt, system_prompt)

        fact_check = output.get("fact_check", {})
        approved_claims = output.get("approved_claims_summary", {})

        summary = fact_check.get("claims_summary", {})
        logs = (
            f"Fact check completado por Veritas para {character_name}. "
            f"Score de confianza global: {fact_check.get('overall_confidence_score')}. "
            f"Status: {fact_check.get('status')}. "
            f"Resumen de Claims: {summary.get('verified', 0)} verified, {summary.get('partial', 0)} partial, "
            f"{summary.get('unverified', 0)} unverified, {summary.get('rejected', 0)} rejected."
        )
        return fact_check, approved_claims, logs

    def verify_manual_script(self, character_name: str, scripts_data: dict, research_data: dict, approved_claims: dict) -> tuple:
        """
        Audita el guion modificado manualmente por el editor para asegurar la veracidad de los hechos relatados.
        Devuelve (fact_check_json_dict, logs_str).
        """
        print(f"[Veritas - Quality Gate Manual] Auditando guion editado para: {character_name}...")

        system_prompt = (
            "Eres Veritas, el auditor de confianza, fact checker y quality gate del ecosistema Hermoso.\n"
            "Tu trabajo ahora es auditar el guion redactado/modificado manualmente por el editor. "
            "Debes contrastar cada hecho y dato del guion frente a la investigación autorizada (approved_claims) "
            "y la investigación general (research_data).\n"
            "Debes asegurar que el editor no haya introducido datos históricos falsos, fechas erróneas o reclamos "
            "sin suficiente sustento. Si detectas alguna falsedad o falta grave de soporte, marca el estado como REJECTED."
        )

        prompt = f"""
        Guion corto y contenidos modificados del editor:
        - Guion Corto: {scripts_data.get('script_short', '')}
        - Newsletter: {scripts_data.get('newsletter', '')}
        - Post LinkedIn: {scripts_data.get('linkedin_post', '')}

        Investigación autorizada (approved_claims):
        {json.dumps(approved_claims, ensure_ascii=False, indent=2)}

        Investigación general detallada (research_data):
        {json.dumps(research_data, ensure_ascii=False, indent=2)}

        Audita el guion. Genera un objeto JSON estructurado con los siguientes campos:
        {{
          "script_audit": {{
            "subject": "{character_name}",
            "overall_accuracy_score": 95, // 0 a 100 de precisión histórica
            "status": "APPROVED", // APPROVED | NEEDS_REVIEW | REJECTED
            "detected_issues": [
              {{
                "issue_description": "Descripción del dato erróneo o no contrastado",
                "severity": "high | medium | low",
                "evidence_contradiction": "Detalle de por qué contradice la investigación"
              }}
            ],
            "notes": "Notas generales de auditoría de Veritas",
            "recommended_next_action": "Aprobar para producción de storyboard"
          }}
        }}
        """

        output = self.client.complete_json(prompt, system_prompt)
        audit = output.get("script_audit", {})
        
        logs = f"Auditoría de guion manual completada por Veritas para {character_name}. Precisión: {audit.get('overall_accuracy_score', 0)}%. Estado: {audit.get('status', 'REJECTED')}."
        print(f"[Veritas - Quality Gate Manual] Auditoría finalizada con estado: {audit.get('status')}")
        
        return audit, logs
