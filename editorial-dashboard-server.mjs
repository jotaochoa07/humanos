import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PORT = Number(process.env.PORT || 3100);

const CATEGORIES = [
  "ENTREPRENEURS", "DESIGNERS", "ARTISTS", "MAKERS", "FOUNDERS", "BUILDERS",
  "INVENTORS", "CREATORS", "SCIENTISTS", "EXPLORERS", "ENGINEERS", "VISIONARIES",
];

function stripMarkdownTitle(content) {
  return String(content || "").replace(/^#.*\r?\n\r?\n/, "").trim();
}

function readJsonIfExists(filePath, fallback = null) {
  if (!existsSync(filePath)) return fallback;
  return JSON.parse(readFileSync(filePath, "utf8"));
}

function getPersonajesRoot() {
  return path.join(__dirname, "personajes");
}

function findEpisodeDirectories() {
  const personasRoot = getPersonajesRoot();
  if (!existsSync(personasRoot)) return [];

  const episodes = [];
  for (const protagonistFolder of readdirSync(personasRoot, { withFileTypes: true }).filter((d) => d.isDirectory())) {
    const protagonistRoot = path.join(personasRoot, protagonistFolder.name);
    for (const episodeDir of readdirSync(protagonistRoot, { withFileTypes: true }).filter((d) => d.isDirectory() && d.name.startsWith("EP"))) {
      const episodePath = path.join(protagonistRoot, episodeDir.name);
      const state = readJsonIfExists(path.join(episodePath, "pipeline_state.json"));
      if (!state || state.status !== "script_pending_review") continue;

      const scriptsPath = path.join(episodePath, "02_SCRIPT", "scripts.json");
      const scriptPath = path.join(episodePath, "02_SCRIPT", "script_short.md");
      const scriptsJson = readJsonIfExists(scriptsPath, {});

      episodes.push({
        protagonistName: protagonistFolder.name.replaceAll("_", " "),
        episodeDir: episodeDir.name,
        episodePath,
        status: state.status,
        scriptShort: existsSync(scriptPath) ? stripMarkdownTitle(readFileSync(scriptPath, "utf8")) : (scriptsJson?.script_short || ""),
        scriptLong: scriptsJson?.script_long || "",
        newsletter: scriptsJson?.newsletter || "",
        twitterThread: scriptsJson?.twitter_thread || "",
        category: scriptsJson?.domain_category || "",
      });
    }
  }

  return episodes.sort((a, b) => a.protagonistName.localeCompare(b.protagonistName));
}

function getEpisodeByPath(episodePath) {
  if (!episodePath) return null;
  const normalized = path.resolve(episodePath);
  const personasRoot = path.resolve(getPersonajesRoot());
  if (!normalized.startsWith(personasRoot)) return null;
  if (!existsSync(normalized)) return null;
  return normalized;
}

function loadEpisodePayload(episodePath) {
  const safePath = getEpisodeByPath(episodePath);
  if (!safePath) return null;
  const state = readJsonIfExists(path.join(safePath, "pipeline_state.json"));
  const scriptsPath = path.join(safePath, "02_SCRIPT", "scripts.json");
  const scriptsJson = readJsonIfExists(scriptsPath, {});
  const protagonistName = path.basename(path.dirname(safePath)).replaceAll("_", " ");
  const scriptPath = path.join(safePath, "02_SCRIPT", "script_short.md");
  const longScriptPath = path.join(safePath, "02_SCRIPT", "script_long.md");
  const newsletterPath = path.join(safePath, "02_SCRIPT", "newsletter.md");
  const twitterPath = path.join(safePath, "02_SCRIPT", "twitter_thread.md");
  const researchDir = path.join(safePath, "01_RESEARCH");
  const storyboardDir = path.join(safePath, "03_STORYBOARD");
  const scriptShort = existsSync(scriptPath) ? stripMarkdownTitle(readFileSync(scriptPath, "utf8")) : (scriptsJson?.script_short || "");
  const readText = (filePath) => (existsSync(filePath) ? readFileSync(filePath, "utf8") : "");
  const readJson = (filePath) => (existsSync(filePath) ? JSON.parse(readFileSync(filePath, "utf8")) : null);

  return {
    protagonistName,
    episodePath: safePath,
    status: state?.status || "unknown",
    scriptShort,
    veritas: {
      factCheck: readJson(path.join(researchDir, "fact_check.json")),
      approvedClaims: readJson(path.join(researchDir, "approved_claims.json")),
      claims: readJson(path.join(researchDir, "claims.json")),
      sources: readText(path.join(researchDir, "sources.md")),
      assetReport: readText(path.join(researchDir, "ASSET_COLLECTION_REPORT.md")),
    },
    gabo: {
      short: scriptShort,
      long: readText(longScriptPath) || (scriptsJson?.script_long || ""),
      newsletter: readText(newsletterPath) || (scriptsJson?.newsletter || ""),
      twitter: readText(twitterPath) || (scriptsJson?.twitter_thread || ""),
    },
    moore: {
      storyboard: readJson(path.join(storyboardDir, "storyboard.json")),
      shotlist: readText(path.join(storyboardDir, "shotlist.md")),
      editingNotes: readText(path.join(storyboardDir, "editing_notes.md")),
      assetGaps: readJson(path.join(storyboardDir, "asset_gaps.json")),
      productionPackage: readJson(path.join(storyboardDir, "production_package.json")),
    },
    scriptsJson,
  };
}

function loadEnv() {
  const env = { ...process.env };
  const envPath = path.join(__dirname, ".env");
  if (!existsSync(envPath)) return env;

  for (const rawLine of readFileSync(envPath, "utf8").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) continue;
    const [key, ...valueParts] = line.split("=");
    env[key.trim()] = valueParts.join("=").trim().replace(/^['\"]|['\"]$/g, "");
  }
  return env;
}

function getSupabaseConfig() {
  const env = loadEnv();
  const url = env.SUPABASE_URL;
  const key = env.SUPABASE_KEY;
  if (!url || !key) throw new Error("Missing SUPABASE_URL or SUPABASE_KEY in .env");
  return { url, key, env };
}

async function readBody(req) {
  let body = "";
  for await (const chunk of req) body += chunk;
  return body ? JSON.parse(body) : {};
}

function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(payload));
}

async function supabaseRequest(endpoint, { method = "GET", body } = {}) {
  const { url, key } = getSupabaseConfig();
  const response = await fetch(`${url}/rest/v1/${endpoint}`, {
    method,
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
      Prefer: method === "PATCH" || method === "POST" ? "return=representation" : "",
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) throw new Error(data?.message || `Supabase request failed: ${response.status}`);
  return data;
}

function startPipeline(protagonistName, humanAngle, domainCategory) {
  const { env } = getSupabaseConfig();
  const child = spawn("python", [
    "run_humanos_mvp.py",
    "--character", protagonistName,
    "--focus", humanAngle,
    "--themes", domainCategory.toLowerCase(),
    "--stage", "write",
  ], {
    cwd: __dirname,
    env,
    shell: false,
    windowsHide: true,
  });

  child.stdout.on("data", (data) => process.stdout.write(`[pipeline:${protagonistName}] ${data}`));
  child.stderr.on("data", (data) => process.stderr.write(`[pipeline:${protagonistName}:err] ${data}`));
  return child;
}

async function handleStories(res) {
  const select = "id,protagonist_name,human_angle,domain_category,editorial_status";
  const endpoint = `humanos_stories?editorial_status=in.(idea,needs_research)&select=${select}&order=protagonist_name.asc`;
  sendJson(res, 200, { stories: await supabaseRequest(endpoint) });
}

async function handleReviewEpisodes(res) {
  sendJson(res, 200, { episodes: findEpisodeDirectories() });
}

async function handleReviewEpisode(req, res, url) {
  const payload = loadEpisodePayload(url.searchParams.get("episodePath"));
  if (!payload) return sendJson(res, 404, { error: "Episode not found" });
  sendJson(res, 200, payload);
}

async function handleStart(req, res) {
  const body = await readBody(req);
  const id = String(body.id || "").trim();
  const protagonistName = String(body.protagonistName || "").trim();
  const humanAngle = String(body.humanAngle || "").trim();
  const domainCategory = String(body.domainCategory || "").trim().toUpperCase();
  const format = String(body.format || "complete").trim();

  if (!id || !protagonistName || !humanAngle || !CATEGORIES.includes(domainCategory)) return sendJson(res, 400, { error: "Invalid story payload" });

  await supabaseRequest(`humanos_stories?id=eq.${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: { editorial_status: "researching", domain_category: domainCategory.toLowerCase(), human_angle: humanAngle },
  });

  const child = startPipeline(protagonistName, humanAngle, domainCategory);
  child.on("exit", async (code) => {
    console.log(`[pipeline:${protagonistName}] exited with code ${code}`);
    if (code !== 0) {
      try {
        await supabaseRequest(`humanos_stories?id=eq.${encodeURIComponent(id)}`, { method: "PATCH", body: { editorial_status: "needs_research" } });
      } catch (error) {
        console.error(`[pipeline:${protagonistName}] failed to restore status`, error);
      }
    }
  });

  sendJson(res, 202, { ok: true, message: "Pipeline started", pid: child.pid, format });
}

async function handleCreateAndStart(req, res) {
  const body = await readBody(req);
  const protagonistName = String(body.protagonistName || "").trim();
  const humanAngle = String(body.humanAngle || "").trim();
  const domainCategory = String(body.domainCategory || "").trim().toUpperCase();
  const format = String(body.format || "complete").trim();

  if (!protagonistName || !humanAngle || !CATEGORIES.includes(domainCategory)) return sendJson(res, 400, { error: "Faltan campos obligatorios" });

  const insertResult = await supabaseRequest("humanos_stories", {
    method: "POST",
    body: { protagonist_name: protagonistName, human_angle: humanAngle, domain_category: domainCategory.toLowerCase(), editorial_status: "researching" },
  });

  const insertedStory = Array.isArray(insertResult) ? insertResult[0] : null;
  const child = startPipeline(protagonistName, humanAngle, domainCategory);
  child.on("exit", async (code) => {
    console.log(`[pipeline:${protagonistName}] exited with code ${code}`);
    if (code !== 0 && insertedStory?.id) {
      try {
        await supabaseRequest(`humanos_stories?id=eq.${encodeURIComponent(insertedStory.id)}`, { method: "PATCH", body: { editorial_status: "needs_research" } });
      } catch (error) {
        console.error(`[pipeline:${protagonistName}] failed to restore status`, error);
      }
    }
  });

  sendJson(res, 202, { ok: true, message: "Personaje creado y pipeline iniciado", pid: child.pid, format });
}

async function handleProduce(req, res) {
  const body = await readBody(req);
  const episodePath = String(body.episodePath || "").trim();
  const protagonistName = String(body.protagonistName || "").trim();
  const scriptShort = String(body.scriptShort || "").trim();
  const payload = loadEpisodePayload(episodePath);
  if (!payload || !protagonistName || !scriptShort) return sendJson(res, 400, { error: "Faltan campos obligatorios" });

  const safePath = getEpisodeByPath(episodePath);
  const scriptDir = path.join(safePath, "02_SCRIPT");
  const scriptShortPath = path.join(scriptDir, "script_short.md");
  const scriptsPath = path.join(scriptDir, "scripts.json");
  const updatedScripts = { ...(payload.scriptsJson || {}), script_short: scriptShort };
  writeFileSync(scriptShortPath, `# Guion Corto: ${protagonistName}\n\n${scriptShort}\n`, "utf8");
  writeFileSync(scriptsPath, JSON.stringify(updatedScripts, null, 2) + "\n", "utf8");

  const child = spawn("python", ["run_humanos_mvp.py", "--character", protagonistName, "--stage", "produce"], {
    cwd: __dirname,
    env: getSupabaseConfig().env,
    shell: false,
    windowsHide: true,
  });

  child.stdout.on("data", (data) => process.stdout.write(`[produce:${protagonistName}] ${data}`));
  child.stderr.on("data", (data) => process.stderr.write(`[produce:${protagonistName}:err] ${data}`));
  child.on("exit", async (code) => {
    console.log(`[produce:${protagonistName}] exited with code ${code}`);
    if (code === 0) {
      try {
        const supabaseStories = await supabaseRequest(`humanos_stories?protagonist_name=eq.${encodeURIComponent(protagonistName)}&select=id`);
        const storyRow = Array.isArray(supabaseStories) ? supabaseStories[0] : null;
        if (storyRow?.id) {
          await supabaseRequest(`humanos_stories?id=eq.${encodeURIComponent(storyRow.id)}`, { method: "PATCH", body: { editorial_status: "researched" } });
        }
      } catch (error) {
        console.error(`[produce:${protagonistName}] failed to update Supabase`, error);
      }
    }
  });

  sendJson(res, 202, { ok: true, message: "Producción iniciada", pid: child.pid });
}

async function serveStatic(res, filePath, contentType) {
  const content = await readFile(filePath);
  res.writeHead(200, { "Content-Type": contentType });
  res.end(content);
}

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url || "/", `http://localhost:${PORT}`);
    if (req.method === "GET" && url.pathname === "/api/stories") return void await handleStories(res);
    if (req.method === "GET" && url.pathname === "/api/review-episodes") return void await handleReviewEpisodes(res);
    if (req.method === "GET" && url.pathname === "/api/review-episode") return void await handleReviewEpisode(req, res, url);
    if (req.method === "POST" && url.pathname === "/api/start") return void await handleStart(req, res);
    if (req.method === "POST" && url.pathname === "/api/create-and-start") return void await handleCreateAndStart(req, res);
    if (req.method === "POST" && url.pathname === "/api/produce") return void await handleProduce(req, res);
    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/editorial")) return void await serveStatic(res, path.join(__dirname, "public", "editorial-dashboard.html"), "text/html; charset=utf-8");
    sendJson(res, 404, { error: "Not found" });
  } catch (error) {
    console.error(error);
    sendJson(res, 500, { error: error.message || "Unexpected error" });
  }
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`HUMANOS Editorial Dashboard running at http://127.0.0.1:${PORT}`);
});
