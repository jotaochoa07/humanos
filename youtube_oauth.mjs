/**
 * youtube_oauth — conexión OAuth con el canal de Jota Growth.
 *
 * Por qué existe
 * --------------
 * Hasta el 2026-08-01 el sistema "aprendía" de métricas generadas con
 * random.randint(). Cuando llegaron los números reales del export de
 * YouTube Studio, la diferencia era de hasta 721x (Jan Koum: el sistema
 * creía 657.002 vistas; la realidad eran 911).
 *
 * El CSV resuelve el pasado pero no el futuro: hay que exportarlo a mano
 * cada vez. Esto conecta el canal de verdad, para que Mark capture solo y
 * Mr. You lea datos frescos sin que nadie descargue nada.
 *
 * Diseño
 * ------
 * - SOLO LECTURA. Los scopes son `readonly`. Este módulo no puede publicar,
 *   editar ni borrar nada del canal aunque quisiera.
 * - Sin dependencias nuevas: fetch nativo de Node 18+. El repo ya evita SDKs.
 * - Los tokens van a `_LAB/youtube_tokens.json`, ya añadido al .gitignore.
 * - El client_secret NUNCA se copia al repo: se lee de su ubicación original
 *   en JotaOS.
 */

import { existsSync, readFileSync, writeFileSync, mkdirSync, readdirSync } from "node:fs";
import path from "node:path";

// Ubicacion del client_secret_*.json. Se puede mover definiendo
// YT_CREDENCIALES en el .env o en el entorno.
const CARPETA_CREDENCIALES =
  process.env.YT_CREDENCIALES ||
  "C:\\JotaOS\\100 - Proyectos\\JOTA AI YOUTUBE\\Reportes_analytics";

// Solo lectura. Deliberado: este sistema mide, no publica.
const SCOPES = [
  "https://www.googleapis.com/auth/yt-analytics.readonly",
  "https://www.googleapis.com/auth/youtube.readonly",
].join(" ");

// URL canonica local: localhost:3100 (decision de Jota, 2026-08-01).
// Este valor YA figura entre los redirect_uris autorizados del cliente OAuth,
// asi que no hace falta tocar nada en Google Cloud.
const REDIRECT =
  process.env.YT_REDIRECT || "http://localhost:3100/api/auth/youtube/callback";

let __estadoCsrf = null;

/* ------------------------------------------------------------------ */
/* Credenciales                                                        */
/* ------------------------------------------------------------------ */

export function cargarCredenciales() {
  if (!existsSync(CARPETA_CREDENCIALES)) {
    throw new Error(`No encuentro la carpeta de credenciales:\n  ${CARPETA_CREDENCIALES}`);
  }
  const archivo = readdirSync(CARPETA_CREDENCIALES)
    .find((f) => f.startsWith("client_secret_") && f.endsWith(".json"));
  if (!archivo) {
    throw new Error(
      `No hay ningun client_secret_*.json en:\n  ${CARPETA_CREDENCIALES}\n` +
      `Descargalo de Google Cloud Console > Credenciales > tu ID de cliente OAuth.`
    );
  }
  const bruto = JSON.parse(readFileSync(path.join(CARPETA_CREDENCIALES, archivo), "utf8"));
  const c = bruto.web || bruto.installed;
  if (!c) throw new Error("El client_secret no tiene bloque 'web' ni 'installed'.");
  return {
    clientId: c.client_id,
    clientSecret: c.client_secret,
    authUri: c.auth_uri || "https://accounts.google.com/o/oauth2/auth",
    tokenUri: c.token_uri || "https://oauth2.googleapis.com/token",
    redirectUris: c.redirect_uris || [],
  };
}

function rutaTokens(baseDir) {
  return path.join(baseDir, "_LAB", "youtube_tokens.json");
}

export function leerTokens(baseDir) {
  const p = rutaTokens(baseDir);
  return existsSync(p) ? JSON.parse(readFileSync(p, "utf8")) : null;
}

function guardarTokens(baseDir, tokens) {
  const dir = path.join(baseDir, "_LAB");
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  writeFileSync(rutaTokens(baseDir), JSON.stringify(tokens, null, 2), "utf8");
}

/* ------------------------------------------------------------------ */
/* Flujo OAuth                                                         */
/* ------------------------------------------------------------------ */

export function urlDeConsentimiento() {
  const c = cargarCredenciales();
  if (!c.redirectUris.includes(REDIRECT)) {
    throw new Error(
      `El redirect ${REDIRECT} no esta autorizado en Google Cloud.\n` +
      `Autorizados: ${c.redirectUris.join(", ")}\n` +
      `Anadilo en Console > Credenciales > URIs de redireccionamiento autorizados.`
    );
  }
  __estadoCsrf = Math.random().toString(36).slice(2) + Date.now().toString(36);
  const q = new URLSearchParams({
    client_id: c.clientId,
    redirect_uri: REDIRECT,
    response_type: "code",
    scope: SCOPES,
    access_type: "offline",     // queremos refresh_token
    prompt: "consent",          // fuerza a que Google lo entregue
    include_granted_scopes: "true",
    state: __estadoCsrf,
  });
  return `${c.authUri}?${q.toString()}`;
}

export async function canjearCodigo(baseDir, code, state) {
  if (__estadoCsrf && state !== __estadoCsrf) {
    throw new Error("El parametro 'state' no coincide. Posible CSRF: se aborta.");
  }
  const c = cargarCredenciales();
  const r = await fetch(c.tokenUri, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id: c.clientId,
      client_secret: c.clientSecret,
      redirect_uri: REDIRECT,
      grant_type: "authorization_code",
    }),
  });
  const d = await r.json();
  if (!r.ok) throw new Error(`Google rechazo el canje: ${JSON.stringify(d)}`);

  const tokens = {
    access_token: d.access_token,
    refresh_token: d.refresh_token || null,
    scope: d.scope,
    expira_en: Date.now() + (d.expires_in || 3600) * 1000,
    obtenido_en: new Date().toISOString(),
  };
  guardarTokens(baseDir, tokens);
  return tokens;
}

async function accessTokenValido(baseDir) {
  const t = leerTokens(baseDir);
  if (!t) throw new Error("SIN_CONEXION");
  if (Date.now() < t.expira_en - 60000) return t.access_token;

  if (!t.refresh_token) {
    throw new Error(
      "El token expiro y no hay refresh_token. Volve a conectar el canal."
    );
  }
  const c = cargarCredenciales();
  const r = await fetch(c.tokenUri, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      refresh_token: t.refresh_token,
      client_id: c.clientId,
      client_secret: c.clientSecret,
      grant_type: "refresh_token",
    }),
  });
  const d = await r.json();
  if (!r.ok) throw new Error(`No se pudo refrescar el token: ${JSON.stringify(d)}`);

  const nuevos = {
    ...t,
    access_token: d.access_token,
    expira_en: Date.now() + (d.expires_in || 3600) * 1000,
    refrescado_en: new Date().toISOString(),
  };
  guardarTokens(baseDir, nuevos);
  return nuevos.access_token;
}

/* ------------------------------------------------------------------ */
/* Consultas                                                           */
/* ------------------------------------------------------------------ */

async function getJson(url, token) {
  const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  const d = await r.json();
  if (!r.ok) {
    throw new Error(`HTTP ${r.status}: ${d?.error?.message || JSON.stringify(d).slice(0, 200)}`);
  }
  return d;
}

export async function estado(baseDir) {
  const t = leerTokens(baseDir);
  if (!t) return { conectado: false, motivo: "No hay tokens. Falta autorizar el canal." };
  try {
    const token = await accessTokenValido(baseDir);
    const d = await getJson(
      "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true",
      token
    );
    const ch = d.items?.[0];
    return {
      conectado: true,
      canal: ch?.snippet?.title,
      canal_id: ch?.id,
      suscriptores: ch?.statistics?.subscriberCount,
      vistas_totales: ch?.statistics?.viewCount,
      videos: ch?.statistics?.videoCount,
      scope: t.scope,
      expira_en: new Date(t.expira_en).toISOString(),
    };
  } catch (e) {
    return { conectado: false, motivo: String(e.message || e) };
  }
}

/**
 * Métricas por video. Incluye lo que el CSV NO trae: retención media real.
 */
export async function metricasPorVideo(baseDir, { desde, hasta } = {}) {
  const token = await accessTokenValido(baseDir);
  const hoy = new Date();
  const fin = hasta || hoy.toISOString().slice(0, 10);
  const ini = desde || new Date(hoy.getTime() - 365 * 864e5).toISOString().slice(0, 10);

  const q = new URLSearchParams({
    ids: "channel==MINE",
    startDate: ini,
    endDate: fin,
    metrics: [
      "views",
      "estimatedMinutesWatched",
      "averageViewDuration",
      "averageViewPercentage",
      "subscribersGained",
      "likes",
      "shares",
      "annotationClickThroughRate",
    ].join(","),
    dimensions: "video",
    sort: "-views",
    maxResults: "50",
  });

  const d = await getJson(
    `https://youtubeanalytics.googleapis.com/v2/reports?${q}`,
    token
  );

  const cols = (d.columnHeaders || []).map((c) => c.name);
  const filas = (d.rows || []).map((fila) =>
    Object.fromEntries(fila.map((v, i) => [cols[i], v]))
  );

  return {
    periodo: { desde: ini, hasta: fin },
    columnas: cols,
    videos: filas,
    nota:
      "averageViewPercentage es dato nativo de YouTube, no derivado. " +
      "El CSV de Studio no lo trae; por eso conectar la API importa.",
  };
}

export const CONFIG = { REDIRECT, SCOPES, CARPETA_CREDENCIALES };
