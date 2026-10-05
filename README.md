# 🌮 mimenu Prospección B2B (Apify + Subagentes)

Sistema de prospección automatizada y generación de prospectos para **mimenu**. 
Permite extraer pequeños negocios de comida (taquerías, cafeterías, pizzerías, fondas) usando **Google Maps Scraper en Apify**, limpiando y validando números de WhatsApp, y clasificando cada prospecto con **Lead Scoring (Score A, B, C)** junto a su guion de apertura comercial personalizado.

---

## 📂 Estructura del Repositorio

```text
prospeccion-mimenu/
├── SKILL.md                     # Definición de la Skill y subagentes para Antigravity
├── README.md                    # Documentación de instalación y uso
├── requirements.txt             # Dependencias de Python (apify-client)
├── .gitignore                   # Protección de datos de clientes y credenciales
├── scripts/
│   └── prospector_engine.py     # Motor en Python de extracción, validación y scoring
└── templates/
    └── pitches.md               # Guiones de apertura para WhatsApp por categoría
```

---

## 🚀 Instalación en Cualquier Computadora con Antigravity

Para tener esta habilidad disponible de forma global en Antigravity en cualquier otra máquina (Windows, Mac o Linux), sigue estos pasos:

### 1. Clonar el repositorio
Abre una terminal en tu nueva computadora y clona este repositorio directamente en la carpeta global de habilidades de Gemini/Antigravity:

* **En Windows (PowerShell):**
  ```powershell
  cd "$env:USERPROFILE\.gemini\config\skills"
  git clone https://github.com/TU_USUARIO/mimenu-prospeccion.git prospeccion-mimenu
  ```

* **En macOS / Linux:**
  ```bash
  cd ~/.gemini/config/skills
  git clone https://github.com/TU_USUARIO/mimenu-prospeccion.git prospeccion-mimenu
  ```

### 2. Instalar dependencias de Python
```bash
pip install -r prospeccion-mimenu/requirements.txt
```

### 3. Configurar tu Token de Apify
Puedes configurarlo como variable de entorno:
```bash
# Windows PowerShell
$env:APIFY_TOKEN="tu_token_de_apify"

# Linux / Mac
export APIFY_TOKEN="tu_token_de_apify"
```
O agregarlo en tu archivo `~/.gemini/antigravity/mcp_config.json`.

---

## 💡 Formas de Uso

### Modo 1: Desde el Chat de Antigravity (Recomendado)
Pídele en lenguaje natural al asistente:
> *"Busca 20 taquerías en Querétaro para mimenu usando la habilidad de prospección."*

Los tres subagentes trabajarán automáticamente:
1. **`mimenu-extractor`**: Consulta Apify Google Maps Scraper.
2. **`mimenu-validador`**: Valida y estandariza números a formato WhatsApp (+52) y descarta cadenas corporativas (ej. Starbucks, Domino's).
3. **`mimenu-calificador`**: Genera la matriz de Score A/B/C y redacta el mensaje de contacto.

---

### Modo 2: Desde la Terminal (Modo Autónomo / Script)
Puedes ejecutar el motor directamente sin abrir el chat:

```powershell
python scripts/prospector_engine.py --location "Roma Norte, CDMX" --category "taquerias" --limit 15 --output "prospectos_roma"
```

Generará dos archivos:
* `prospectos_roma.csv`: Archivo listo para importar en Excel o tu CRM.
* `prospectos_roma.json`: Datos estructurados completos.
