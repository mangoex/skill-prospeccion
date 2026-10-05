---
name: prospeccion-mimenu
description: Sistema integral de prospección B2B para mimenu con conectores de Apify, extracción de negocios locales de comida (Google Maps/Instagram), y subagentes de validación y calificación de prospectos (Lead Scoring).
---

# Prospección mimenu (B2B Food & Beverage Lead Generation)

Habilidad diseñada para identificar, extraer, validar y calificar prospectos de pequeños y medianos negocios de comida (fondas, taquerías, cafeterías, pizzerías, dark kitchens, reposterías, restaurantes familiares) para **mimenu**.

---

## 1. Perfil de Cliente Ideal (ICP - Ideal Customer Profile) de mimenu

El objetivo de **mimenu** es digitalizar negocios gastronómicos que sufren con cartas físicas, fotos de mala calidad en WhatsApp o PDFs pesados que no se actualizan.

### Criterios de Calificación (Lead Scoring)

| Calificación | Perfil del Negocio | Señales Clave | Acción Recomendada |
| :--- | :--- | :--- | :--- |
| **Score A (Oro / Hot Lead)** | Pequeño/mediano negocio con alto flujo y poca digitalización | • Teléfono móvil / WhatsApp disponible<br>• Sin sitio web o con menú en foto estática/pizarra en Google Maps<br>• Más de 15 reseñas y activo en los últimos 30 días<br>• Comida rápida, taquería, cafetería, fonda o pizzería local | **Pitch directo por WhatsApp** con demo interactiva de su menú digitalizado. |
| **Score B (Plata / Warm Lead)** | Negocio con digitalización precaria o desactualizada | • Tienen Linktree o PDF alojado en Google Drive<br>• Redes sociales con baja interacción o menú desactualizado<br>• Teléfono fijo o sin WhatsApp verificado inmediatamente | **Investigación secundaria**: Buscar contacto de encargado/dueño en Instagram o llamada corta. |
| **Score C (Descarte / Incompatible)** | Cadenas, franquicias o locales inactivos | • Franquicias corporativas (Starbucks, Domino's, etc.)<br>• Más de 6 meses sin reseñas o marcado como cerrado<br>• Sin teléfono de contacto | **Descartar**: No invertir tiempo ni créditos. |

---

## 2. Arquitectura de Subagentes Especializados

Para garantizar prospección limpia y efectiva, se divide la labor en tres subagentes:

### Subagente 1: `mimenu-lead-hunter` (Extractor & Conector)
* **Objetivo:** Ejecutar la extracción de datos geolocalizados mediante Apify (Google Maps Scraper o Instagram Scraper).
* **Parámetros de búsqueda:**
  * Zona geográfica: Ciudad, colonia, código postal o radio (ej. *"Roma Norte, CDMX"*, *"Providencia, Guadalajara"*, *"Centro, Monterrey"*).
  * Categorías: `taqueria`, `cafeteria`, `fonda`, `pizzeria`, `hamburguesas`, `reposteria`, `antojitos`.
* **Datos recolectados:** Nombre, dirección, coordenadas, teléfono, web, número de reseñas, calificación promedio, enlaces a fotos de menú.

### Subagente 2: `mimenu-validador` (Higiene & Estado de Negocio)
* **Objetivo:** Filtrar prospectos "basura" antes de que lleguen a la etapa comercial.
* **Reglas de validación:**
  1. **Formato telefónico E.164:** Normalizar números (ej. para México prefijo `+52`, 10 dígitos locales). Identificar si es móvil o fijo.
  2. **Actividad reciente:** Comprobar si tiene actividad comercial en los últimos 60 días para descartar locales cerrados.
  3. **Ausencia de soluciones avanzadas:** Filtrar cadenas con software propietario cerrado.

### Subagente 3: `mimenu-calificador` (Lead Scoring & Pitch Personalizado)
* **Objetivo:** Categorizar en Score A, B o C y generar el gancho de venta (Copy / Pitch) personalizado.
* **Output esperado:**
  * Ficha de prospecto con Score.
  * Punto de dolor identificado (ej. *"Tienen 120 fotos en Google Maps pero ninguna carta digital legible"*).
  * Mensaje inicial personalizado para WhatsApp (corto, empático y orientado a aportar valor inmediato).

---

## 3. Integración con Apify

### Actores Recomendados en Apify
1. **Google Maps Scraper** (`compass/crawler-google-places` o `tri_angle/google-maps-scraper`):
   * Extrae directamente datos de contacto, menús, fotos y reseñas.
2. **Instagram Scraper** (`apify/instagram-scraper`):
   * Extrae la bio de perfiles locales de comida y teléfonos en el botón de contacto.

### Modos de Ejecución
1. **Vía Script Python:** `python scripts/prospector_engine.py --location "Roma Norte, CDMX" --category "taqueria" --limit 20`
   * Si `APIFY_TOKEN` está presente en las variables de entorno, invoca la API en vivo.
   * Si no hay token, el motor activa el **Modo Simulación / Demo**, permitiendo probar todo el pipeline de validación y calificación con datos estructurados de prueba.
2. **Vía MCP Server:** Usando la herramienta de Apify en el archivo de configuración `mcp_config.json`.

---

## 4. Flujo de Trabajo Operativo (SOP)

1. **Definir Target:** Indicar ciudad/zona y tipo de comida a prospectar.
2. **Extracción:** Invocar al extractor o ejecutar `prospector_engine.py`.
3. **Validación:** El subagente validador descarta registros incompletos o inactivos.
4. **Calificación:** El subagente calificador genera la tabla de prospectos con su Score (A/B/C) y el mensaje de apertura sugerido.
5. **Exportación:** Los prospectos validados se guardan en formato CSV/JSON para alimentar el CRM o enviar las conversaciones por WhatsApp.
