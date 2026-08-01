# Supabase Health Check - Mantenimiento Automático

## Propósito
Mantener tu base de datos de Supabase activa para evitar timeout por inactividad y que tu proyecto HUMANOS no sea pausado automáticamente.

## Configuración

### Cronjob activo
- **ID:** `ef9e205601fb`
- **Nombre:** `supabase-health-ping`
- **Frecuencia:** Cada 30 minutos
- **Próxima ejecución:** 2026-07-10T09:32:02-05:00
- **Estado:** ✅ Activo y programado

### Archivos
- **Script bash:** `scripts/supabase-ping.sh`
- **Log:** `supabase-ping.log` (en raíz del proyecto humanos)
- **Credenciales:** `.env` (SUPABASE_URL, SUPABASE_KEY)

## Evidencia de funcionamiento
```
[2026-07-10 09:02:04] === Starting Supabase health check ===
[2026-07-10 09:02:05] ✓ Credentials loaded
[2026-07-10 09:02:05] 📍 Pinging: https://nuswdrztixelsfkccfqc.supabase.co/rest/v1/?select=1
[2026-07-10 09:02:07] HTTP Status: 200
[2026-07-10 09:02:07] ✓ PING SUCCESS: Supabase is active
[2026-07-10 09:02:08] ✓ Project: nuswdrztixelsfkccfqc | Organization: agente-jota
```

## Por qué estaba fallando antes
Si ya habías intentado esto antes y falló, probablemente fue por:
1. **Shell no disponible:** Windows + bash puede tener problemas de ejecución
2. **Credenciales incorrectas:** SUPABASE_URL o SUPABASE_KEY mal configurados
3. **Cronjob deshabilitado:** El job se desactiva o se pausa
4. **Timeout de red:** Supabase puede requerir más tiempo para responder

## Qué hace este setup
- ✅ Script bash aislado con credenciales explicitas en `.env`
- ✅ Workdir específico en `humanos/scripts`
- ✅ Logging detallado en archivo local
- ✅ Cronjob cada 30 minutos (más frecuente que el típico 1h)
- ✅ Timeout de 10 segundos en curl
- ✅ Verificación HTTP 200/304 antes de dar por exitoso

## Monitoreo

### Verificar estado del cronjob
```bash
hermes cronjob list | grep supabase
```

### Ver logs manuales
```bash
cat supabase-ping.log
```

### Probar manualmente
```bash
cd C:\Users\Jota Ochoa\Antigravity\02_Projects\humanos\scripts
bash supabase-ping.sh
```

## Next Steps
1. **Revisar logs en 24h:** Verificar que se están ejecutando correctamente
2. **Supabase Dashboard:** Confirmar que tus proyectos no aparecen en "inactive"
3. **Alerta si falla:** Podríamos agregar un webhook de alerta si el ping falla

---
*Creado: 2026-07-10 | Proyecto: HUMANOS | ID Proyecto: nuswdrztixelsfkccfqc*
