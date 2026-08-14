#!/usr/bin/env bash
# Preservacion Git — HUMANOS / Creativity Lab
# Rama: migration/preserve-2026-08-10 · NO hace push · NO toca main
# USO (Windows): clic derecho en la carpeta 'humanos' -> "Git Bash Here" -> bash commit_preservacion.sh
set -euo pipefail
if [ ! -d .git ]; then echo "ERROR: corre esto DENTRO de la carpeta 'humanos' (donde esta .git)."; exit 1; fi

echo "== 0) Verificando locks de git =="
lock_files="$(find .git -name '*.lock' -print 2>/dev/null || true)"
if [[ -n "$lock_files" ]]; then
  if ! command -v ps >/dev/null 2>&1; then
    echo "!! ABORT: no se puede verificar si hay otro proceso Git activo; no se borraran locks." >&2
    exit 1
  fi
  if ! process_snapshot="$(ps -eo pid=,args= 2>/dev/null)"; then
    echo "!! ABORT: fallo la verificacion de procesos Git; no se borraran locks." >&2
    exit 1
  fi
  git_processes="$(printf '%s\n' "$process_snapshot" | awk -v self="$$" '
    {
      pid = $1
      $1 = ""
      cmd = $0
      if (pid != self && (cmd ~ /(^|[[:space:]\/])git([[:space:]]|$)/ || cmd ~ /(^|[[:space:]\/])git-[^[:space:]]+/)) {
        print pid cmd
      }
    }
  ')"
  if [[ -n "$git_processes" ]]; then
    echo "!! ABORT: hay otro proceso Git activo; no se borraran locks:" >&2
    printf '%s\n' "$git_processes" >&2
    exit 1
  fi
  echo "   no se detecto otro proceso Git; borrando locks:"
  printf '%s\n' "$lock_files"
  find .git -name '*.lock' -delete
else
  echo "   no hay locks Git para borrar."
fi
echo "   locks restantes: $(find .git -name '*.lock' 2>/dev/null | wc -l)"

git config user.name  "Jota Ochoa"
git config user.email "jotaochoa07@gmail.com"

git show-ref --verify --quiet refs/heads/migration/preserve-2026-08-10 || git branch migration/preserve-2026-08-10
git checkout migration/preserve-2026-08-10
echo "   rama actual: $(git rev-parse --abbrev-ref HEAD)"
echo "   main sigue en: $(git rev-parse main)"

COMMIT_HASHES=()

is_allowed_path () {
  local path="$1"; shift
  local allowed
  for allowed in "$@"; do
    if [[ "$allowed" == */ ]]; then
      [[ "$path" == "$allowed"* ]] && return 0
    else
      [[ "$path" == "$allowed" ]] && return 0
    fi
  done
  return 1
}

commit_group () {
  local msg="$1"; shift
  local staged_before staged_after path commit_hash
  local reuse_existing_staging=false
  local -a allowed_paths=("$@")

  staged_before="$(git diff --cached --name-only)"
  if [[ -n "$staged_before" ]]; then
    if [[ "$msg" == "feat(agents): preserve recent agents and doctrine" ]]; then
      local staging_matches_commit_1=true
      while IFS= read -r path; do
        [[ -z "$path" ]] && continue
        if ! is_allowed_path "$path" "${allowed_paths[@]}"; then
          staging_matches_commit_1=false
          break
        fi
      done <<< "$staged_before"
      for path in mr_you.py canal.py apify_client.py env_boot.py verificar_agentes.py; do
        if ! grep -Fxq -- "$path" <<< "$staged_before"; then
          staging_matches_commit_1=false
          break
        fi
      done
      if printf '%s\n' "$staged_before" | grep -Eiq '(^|/)(node_modules|__pycache__)/|\.env|token|metrics_history\.json|_BACKUP|channel_daily|channel_metrics|youtube_video_map|\.log$'; then
        staging_matches_commit_1=false
      fi
      if [[ "$staging_matches_commit_1" == true ]]; then
        echo "Staging previo coincide exactamente con Commit 1. Se conserva y continúa."
        reuse_existing_staging=true
      else
        echo "!! ABORT: el staging previo no coincide exactamente con la allowlist de Commit 1. No se hara unstage automatico:" >&2
        printf '%s\n' "$staged_before" >&2
        return 1
      fi
    else
      echo "!! ABORT: hay archivos staged inesperados antes de '$msg'. No se hara unstage automatico:" >&2
      printf '%s\n' "$staged_before" >&2
      return 1
    fi
  fi

  if [[ "$reuse_existing_staging" == false ]]; then
    git add -- "$@" 2>/dev/null
  fi
  echo "---- STAGED para: $msg ----"
  staged_after="$(git diff --cached --name-only)"
  printf '%s\n' "$staged_after"
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    if ! is_allowed_path "$path" "${allowed_paths[@]}"; then
      echo "!! ABORT: archivo fuera de la lista permitida para '$msg': $path" >&2
      echo "   El staging se conserva intacto; no se hara unstage automatico." >&2
      return 1
    fi
  done <<< "$staged_after"
  if printf '%s\n' "$staged_after" | grep -Eiq '(^|/)(node_modules|__pycache__)/|\.env|token|metrics_history\.json|_BACKUP|channel_daily|channel_metrics|youtube_video_map|\.log$'; then
    echo "!! ABORT: archivo prohibido. El staging se conserva intacto; no se hara unstage automatico." >&2
    return 1
  fi
  git commit -q -m "$msg" \
    -m "Snapshot de preservacion (sin limpieza de contenido)."
  commit_hash="$(git rev-parse HEAD)"
  COMMIT_HASHES+=("$commit_hash")
  echo ">> commit: $commit_hash"
}

echo; echo "===== COMMIT 1 ====="
commit_group "feat(agents): preserve recent agents and doctrine" \
  agents/ mr_you.py canal.py apify_client.py env_boot.py verificar_agentes.py

echo; echo "===== COMMIT 2 ====="
commit_group "feat(rights): preserve rights and asset traceability" \
  derechos.py archivo_historico.py registrar_assets.py asset_collector.py \
  "Buscar Archivo Lamborghini.bat" "Buscar Fotos Lamborghini.bat" \
  "Bajar Seleccion Lamborghini.bat" "Registrar Assets Lamborghini.bat"

echo; echo "===== COMMIT 3 ====="
commit_group "feat(ep0004): preserve EP0004 production system" \
  moore_largo.py kling_client.py humanizer_agent.py moore.py \
  claude_improvement/_run_pipeline_ep0004.py claude_improvement/_run_veritas_talese_ep0004.py \
  "Cerrar Episodio Lamborghini.bat" "Generar Video IA Lamborghini.bat" "Buscar Video Lamborghini.bat"

echo; echo "===== COMMIT 4 ====="
commit_group "docs(editorial): preserve editorial system and recent knowledge" \
  AGENTS.md HUMANIZER-EVALUATION.md _LAB/CREATOR_CHANGELOG.md \
  public/editorial-dashboard.html editorial-dashboard-server.mjs run_humanos_mvp.py talese.py \
  claude_improvement/AUDITORIA_ALINEACION.md claude_improvement/AUDITORIA_DERECHOS.json \
  claude_improvement/AUDITORIA_EP0004_GUION_LARGO.md claude_improvement/BTS_SESSION_LOG.md \
  claude_improvement/COLA_SIN_CLAUDE.md claude_improvement/PROMPT_RETOMAR_20260807.md \
  claude_improvement/SESION_20260806.md claude_improvement/SESION_20260809.md

echo; echo "===== RESULTADO ====="
echo "rama actual: $(git rev-parse --abbrev-ref HEAD)"
for i in "${!COMMIT_HASHES[@]}"; do
  echo "hash commit $((i + 1)): ${COMMIT_HASHES[$i]}"
done
echo "git log --oneline -5"
git log --oneline -5
echo "git status --short"
git status --short
echo "CONFIRMACION: no hubo push."
