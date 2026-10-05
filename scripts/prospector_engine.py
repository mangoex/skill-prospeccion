"""
Motor de Prospección, Validación y Calificación de Leads para mimenu.
Soporta integración directa con Apify (Google Maps Scraper) o modo demostración/simulación.
"""

import os
import sys
import re
import json
import csv
import argparse
from typing import List, Dict, Any, Optional

# Asegurar soporte de caracteres especiales y emojis en la consola de Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from apify_client import ApifyClient
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False


# Franquicias y cadenas conocidas a filtrar automáticamente (Score C)
EXCLUDED_CHAINS = [
    "mcdonald's", "mcdonalds", "burger king", "kfc", "subway", 
    "starbucks", "domino's pizza", "dominos", "pizza hut", 
    "little caesars", "carl's jr", "toks", "vips", "sanborns",
    "chili's", "applebee's", "oxxo", "seven eleven", "7-eleven"
]


def clean_phone_number(raw_phone: str, default_country_code: str = "+52") -> Dict[str, Any]:
    """
    Normaliza un número de teléfono a formato internacional E.164.
    Identifica si parece un número móvil apto para WhatsApp.
    """
    if not raw_phone:
        return {"valid": False, "formatted": None, "is_mobile": False, "reason": "Sin teléfono"}
    
    # Remover caracteres no numéricos excepto '+'
    digits_only = re.sub(r"[^\d+]", "", raw_phone)
    digits_no_plus = re.sub(r"[^\d]", "", digits_only)

    if len(digits_no_plus) < 8:
        return {"valid": False, "formatted": raw_phone, "is_mobile": False, "reason": "Longitud insuficiente"}

    # Caso México (10 dígitos locales)
    if len(digits_no_plus) == 10:
        formatted = f"{default_country_code}{digits_no_plus}"
        # En México, la mayoría de números móviles inician con dígitos 1-9 tras la lada
        return {"valid": True, "formatted": formatted, "is_mobile": True, "reason": "OK"}
    elif len(digits_no_plus) == 12 and digits_no_plus.startswith("52"):
        formatted = f"+{digits_no_plus}"
        return {"valid": True, "formatted": formatted, "is_mobile": True, "reason": "OK"}
    elif digits_only.startswith("+"):
        return {"valid": True, "formatted": digits_only, "is_mobile": True, "reason": "OK Internacional"}
    
    return {"valid": True, "formatted": f"+{digits_no_plus}", "is_mobile": False, "reason": "Genérico"}


def validate_lead(raw_lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Subagente Validador:
    Verifica que el negocio esté activo, no sea franquicia descartable y tenga contacto utilizable.
    """
    title = (raw_lead.get("title") or raw_lead.get("name") or "").strip()
    title_lower = title.lower()

    # 1. Filtro de cadenas corporativas
    for chain in EXCLUDED_CHAINS:
        if chain in title_lower:
            return {
                **raw_lead,
                "is_valid": False,
                "discard_reason": f"Cadena corporativa detectada: {chain}",
                "lead_score": "C"
            }

    # 2. Validación de estado operativo
    is_permanently_closed = raw_lead.get("permanentlyClosed", False) or raw_lead.get("isTemporarilyClosed", False)
    if is_permanently_closed:
        return {
            **raw_lead,
            "is_valid": False,
            "discard_reason": "Negocio cerrado temporal o permanentemente",
            "lead_score": "C"
        }

    # 3. Validación y formato de teléfono
    raw_phone = raw_lead.get("phone") or raw_lead.get("phoneUnformatted") or ""
    phone_info = clean_phone_number(raw_phone)
    if not phone_info["valid"]:
        return {
            **raw_lead,
            "is_valid": False,
            "phone_formatted": None,
            "discard_reason": f"Teléfono no válido ({phone_info['reason']})",
            "lead_score": "C"
        }

    return {
        **raw_lead,
        "is_valid": True,
        "phone_formatted": phone_info["formatted"],
        "is_mobile": phone_info["is_mobile"],
        "discard_reason": None
    }


def qualify_lead(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Subagente Calificador (Lead Scoring para mimenu):
    Determina si es Score A, B o C y genera el pitch comercial de WhatsApp.
    """
    if not lead.get("is_valid"):
        lead["lead_score"] = "C"
        lead["pitch"] = None
        return lead

    reviews_count = lead.get("reviewsCount") or lead.get("reviews_count") or lead.get("userRatingsTotal") or 0
    rating = lead.get("totalScore") or lead.get("rating") or lead.get("stars") or 0.0
    website = (lead.get("website") or "").strip().lower()
    menu_url = (lead.get("menu") or lead.get("menuUrl") or "").strip().lower()
    category = lead.get("categoryName") or lead.get("subTitle") or "Comida"
    name = lead.get("title") or lead.get("name") or "Negocio"

    has_own_website = bool(website and not any(x in website for x in ["facebook.com", "instagram.com", "wa.me", "linktr.ee"]))
    has_digital_menu = bool(menu_url or "mimenu" in website)

    # Evaluación de Score
    if not has_own_website and not has_digital_menu and reviews_count >= 10:
        score = "A"
        opportunity = "Negocio con alto flujo y carta física/foto estática. Prospecto de oro para mimenu."
    elif not has_own_website or "linktr.ee" in website or "drive.google" in menu_url:
        score = "B"
        opportunity = "Digitalización rudimentaria (PDF o linktree). Candidato para migración a mimenu."
    else:
        score = "B"
        opportunity = "Cuenta con presencia web, verificar si la experiencia del menú móvil es optimizable."

    # Generación de Pitch personalizado para WhatsApp
    is_tacos = any(x in category.lower() or x in name.lower() for x in ["taco", "taquer"])
    demo_url = "https://tacos.mimenu.onl" if is_tacos else "https://mimenu.onl"

    if is_tacos:
        pitch = (
            f"¡Hola {name}! 👋 Vi las excelentes opiniones que tienen en Google Maps sobre sus tacos ({reviews_count} reseñas). "
            f"Les comparto una herramienta pensada para taquerías: mimenu no es solo una carta digital, es también su punto de venta "
            f"y sistema de pedidos, todo configurable y personalizable 100% desde su celular. "
            f"Pueden probar la demo en vivo en 1 minuto aquí: 👉 {demo_url} "
            f"Es totalmente gratis para probar. Cualquier duda sobre cómo montarlo, por aquí lo platicamos con gusto. 🌮🙌"
        )
    else:
        pitch = (
            f"¡Hola {name}! 👋 Vi las excelentes opiniones que tienen en Google Maps sobre su comida ({reviews_count} reseñas). "
            f"En mimenu ayudamos a negocios de {category} a tener su menú interactivo, punto de venta y toma de pedidos directo desde el celular. "
            f"Pueden ver una demo en vivo aquí: 👉 {demo_url} "
            f"Es gratis para probar y cualquier duda lo platicamos con gusto."
        )

    lead["reviewsCount"] = reviews_count
    lead["rating"] = rating
    lead["lead_score"] = score
    lead["opportunity_summary"] = opportunity
    lead["pitch"] = pitch
    return lead


def get_mock_leads(location: str, category: str) -> List[Dict[str, Any]]:
    """Genera datos sintéticos realistas para pruebas y demostración."""
    return [
        {
            "title": f"Tacos y Antojitos Don Pepe ({location})",
            "categoryName": "Taquería",
            "phone": "55 1234 5678",
            "address": f"Calle Juárez #45, {location}",
            "reviewsCount": 84,
            "rating": 4.6,
            "website": "",
            "menuUrl": "",
            "permanentlyClosed": False
        },
        {
            "title": f"Café & Repostería La Esquina ({location})",
            "categoryName": "Cafetería",
            "phone": "+525598765432",
            "address": f"Av. Hidalgo #102, {location}",
            "reviewsCount": 142,
            "rating": 4.8,
            "website": "https://instagram.com/cafelaesquina",
            "menuUrl": "https://drive.google.com/file/d/123xyz/view",
            "permanentlyClosed": False
        },
        {
            "title": f"Fonda Doña Rosa ({location})",
            "categoryName": "Fonda de comida corrida",
            "phone": "5555112233",
            "address": f"Calle Morelos #12, {location}",
            "reviewsCount": 35,
            "rating": 4.5,
            "website": "",
            "menuUrl": "",
            "permanentlyClosed": False
        },
        {
            "title": f"Starbucks Coffee - Sucursal {location}",
            "categoryName": "Cafetería",
            "phone": "5550001111",
            "address": f"Plaza Central Local 4, {location}",
            "reviewsCount": 420,
            "rating": 4.2,
            "website": "https://www.starbucks.com.mx",
            "menuUrl": "https://www.starbucks.com.mx/menu",
            "permanentlyClosed": False
        },
        {
            "title": f"Pizzería Artesanal Napolitana ({location})",
            "categoryName": "Pizzería",
            "phone": "55 4433 2211",
            "address": f"Calle Pino #88, {location}",
            "reviewsCount": 67,
            "rating": 4.7,
            "website": "https://linktr.ee/pizzanapolitana",
            "menuUrl": "",
            "permanentlyClosed": False
        },
        {
            "title": f"Cenaduría Antojos Cerrados ({location})",
            "categoryName": "Restaurante mexicano",
            "phone": "55 9988 7766",
            "address": f"Callejón 5, {location}",
            "reviewsCount": 12,
            "rating": 3.8,
            "website": "",
            "menuUrl": "",
            "permanentlyClosed": True
        }
    ]


def run_apify_google_maps_scraper(location: str, category: str, limit: int, token: str) -> List[Dict[str, Any]]:
    """Ejecuta el actor Google Maps Scraper en Apify."""
    if not APIFY_AVAILABLE:
        raise ImportError("La librería 'apify-client' no está instalada. Instálala con 'pip install apify-client'.")
    
    client = ApifyClient(token)
    run_input = {
        "searchStringsArray": [f"{category} en {location}"],
        "maxCrawledPlacesPerSearch": limit,
        "language": "es",
        "skipClosedPlaces": True,
        "allPlacesNoSearch": False
    }

    print(f"📡 Iniciando Actor de Apify (compass/crawler-google-places)... Búsqueda: '{category} en {location}' (Límite: {limit})")
    run = client.actor("compass/crawler-google-places").call(run_input=run_input)
    dataset_id = getattr(run, "default_dataset_id", None) or (run.get("defaultDatasetId") if isinstance(run, dict) else None)
    dataset_items = client.dataset(dataset_id).list_items().items
    return [dict(item) if not isinstance(item, dict) else item for item in dataset_items]


def process_leads(raw_leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Procesa los prospectos por el pipeline de Validación y Calificación."""
    results = []
    for raw in raw_leads:
        validated = validate_lead(raw)
        qualified = qualify_lead(validated)
        results.append(qualified)
    return results


def save_reports(leads: List[Dict[str, Any]], output_prefix: str = "prospectos_mimenu"):
    """Guarda los resultados en JSON y CSV."""
    json_path = f"{output_prefix}.json"
    csv_path = f"{output_prefix}.csv"

    # Guardar JSON completo
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)

    # Guardar CSV resumido para uso comercial / CRM
    fieldnames = ["lead_score", "title", "categoryName", "phone_formatted", "reviewsCount", "rating", "website", "opportunity_summary", "pitch", "discard_reason"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for lead in leads:
            writer.writerow(lead)

    return json_path, csv_path


def main():
    parser = argparse.ArgumentParser(description="Motor de Prospección para mimenu con Apify y Subagentes")
    parser.add_argument("--location", type=str, default="Roma Norte, CDMX", help="Ubicación o zona geográfica a prospectar")
    parser.add_argument("--category", type=str, default="restaurantes y comida", help="Tipo de comida o categoría")
    parser.add_argument("--limit", type=int, default=10, help="Cantidad máxima de prospectos a extraer")
    parser.add_argument("--mock", action="store_true", help="Forzar ejecución en modo simulación con datos de prueba")
    parser.add_argument("--output", type=str, default="prospectos_mimenu", help="Prefijo de los archivos de salida")

    args = parser.parse_args()
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        mcp_config_path = r"C:\Users\Miguel Gonzalez\.gemini\antigravity\mcp_config.json"
        if os.path.exists(mcp_config_path):
            try:
                with open(mcp_config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    token = cfg.get("mcpServers", {}).get("apify", {}).get("env", {}).get("APIFY_TOKEN")
            except Exception:
                pass

    print("=" * 60)
    print("🚀 MOTOR DE PROSPECCIÓN mimenu (B2B Food & Beverage)")
    print(f"📍 Zona objetivo: {args.location}")
    print(f"🍽️ Categoría: {args.category}")
    print(f"🎯 Límite: {args.limit}")
    print("=" * 60)

    if token and not args.mock:
        try:
            raw_leads = run_apify_google_maps_scraper(args.location, args.category, args.limit, token)
        except Exception as e:
            print(f"⚠️ Error al conectar con Apify: {e}. Cambiando automáticamente a modo simulación...")
            raw_leads = get_mock_leads(args.location, args.category)
    else:
        if not token:
            print("ℹ️ Nota: No se detectó 'APIFY_TOKEN' en variables de entorno. Ejecutando en Modo Simulación.")
        raw_leads = get_mock_leads(args.location, args.category)

    print(f"\n⚙️ Procesando {len(raw_leads)} prospectos a través de Subagentes de Validación y Calificación...")
    processed_leads = process_leads(raw_leads)

    # Resumen
    score_a = [l for l in processed_leads if l.get("lead_score") == "A"]
    score_b = [l for l in processed_leads if l.get("lead_score") == "B"]
    score_c = [l for l in processed_leads if l.get("lead_score") == "C"]

    print("\n" + "=" * 60)
    print("📊 RESULTADOS DE LA CALIFICACIÓN (LEAD SCORING):")
    print(f"🥇 Score A (Oro / Listos para pitch): {len(score_a)}")
    print(f"🥈 Score B (Plata / Calientes):       {len(score_b)}")
    print(f"❌ Score C (Descartados / Cadenas):   {len(score_c)}")
    print("=" * 60)

    for idx, lead in enumerate(score_a + score_b, 1):
        print(f"\n[{lead['lead_score']}] #{idx} {lead.get('title')}")
        print(f"   📞 Teléfono WhatsApp: {lead.get('phone_formatted')}")
        print(f"   ⭐ Reseñas: {lead.get('reviewsCount')} ({lead.get('rating')} estrellas)")
        print(f"   💡 Oportunidad: {lead.get('opportunity_summary')}")
        print(f"   💬 Pitch WhatsApp:\n   \"{lead.get('pitch')}\"")

    json_path, csv_path = save_reports(processed_leads, args.output)
    print("\n" + "=" * 60)
    print(f"💾 Reportes exportados exitosamente:")
    print(f"   • CSV (Listo para CRM/Excel): {csv_path}")
    print(f"   • JSON (Datos crudos completos): {json_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
