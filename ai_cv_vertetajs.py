"""
AI darbināts CV vērtētājs (Gemini Flash 2.5 + Python)
Autors: Kirills Brjuhoveckis
Datums: 2025
Apraksts:
  Šī Python lietotne izmanto Gemini Flash 2.5 modeli, lai salīdzinātu darba aprakstu (JD)
  ar vairāku kandidātu CV tekstiem un novērtētu to atbilstības līmeni.
  Rezultāts tiek saglabāts JSON un Markdown formātā ar skaidriem HR secinājumiem.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from openai import OpenAI

# ------------------------------------------------------------
# KONFIGURĀCIJA
# ------------------------------------------------------------
MODEL_NAME = "gemini-2.5-flash"   # Var nomainīt uz "gemini-2.5-flash", ja pieejams
TEMPERATURE = 0.3
API_KEY = os.getenv("OPENAI_API_KEY")  # API atslēga no vides mainīgā

# Izveido nepieciešamās mapes
Path("outputs").mkdir(exist_ok=True)
Path("sample_inputs").mkdir(exist_ok=True)

# ------------------------------------------------------------
# PALĪG FUNKCIJAS
# ------------------------------------------------------------
def nolasit_failu(cels: str) -> str:
    """Nolasa teksta failu un atgriež saturu kā virkni."""
    try:
        with open(cels, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"⚠️ Nevar atrast failu: {cels}")
        return ""

def izveidot_promptu(jd_texts: str, cv_texts: str) -> str:
    """Izveido sākotnējo Gemini promptu, apvienojot JD un CV tekstus."""
    prompt = f"""
Tu esi HR speciālists, kas vērtē kandidātu CV atbilstību darba aprakstam (JD).
Analizē abus tekstus un sniedz precīzu JSON atbildi ar šādu struktūru:
{{
  "match_score": 0-100,
  "summary": "Īss apraksts, cik labi CV atbilst JD.",
  "strengths": ["Galvenās prasmes/pieredze no CV, kas atbilst JD"],
  "missing_requirements": ["Svarīgas JD prasības, kas CV nav redzamas"],
  "verdict": "strong match | possible match | not a match"
}}

=== DARBA APRAKSTS ===
{jd_texts}

=== KANDIDĀTA CV ===
{cv_texts}
"""
    with open("prompt.md", "w", encoding="utf-8") as f:
        f.write(prompt.strip())
    return prompt.strip()

def izsaukt_modeli(prompt: str) -> dict:
    """Izsauc Gemini modeli un atgriež JSON atbildi ar rezultātiem."""
    client = OpenAI(api_key=API_KEY)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            messages=[
                {"role": "system", "content": "Tu esi HR analītiķis, kas vērtē CV atbilstību JD."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        rezultata_teksts = response.choices[0].message.content
        try:
            return json.loads(rezultata_teksts)
        except json.JSONDecodeError:
            print("⚠️ Brīdinājums: Modelis neatgrieza derīgu JSON. Saglabāju kā neapstrādātu tekstu.")
            return {"error": "Invalid JSON", "raw_response": rezultata_teksts}

    except Exception as e:
        print(f"❌ Kļūda, izsaucot modeli: {e}")
        return {"error": str(e)}

def saglabat_json(dati: dict, fails: str):
    """Saglabā datus JSON failā."""
    with open(fails, "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, indent=2)

def genereet_parskatu(dati: dict, fails: str):
    """Izveido Markdown pārskatu no JSON rezultātiem."""
    parskats = f"""# CV Atbilstības Pārskats

**Datums:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Atbilstības punktu skaits:** {dati.get('match_score', 'N/A')}

---

### 📝 Kopsavilkums
{dati.get('summary', 'Nav kopsavilkuma.')}

---

### ✅ Stiprās puses
{"".join(f"- {s}\n" for s in dati.get('strengths', [])) or "Nav norādīts."}

---

### ⚠️ Trūkstošās prasības
{"".join(f"- {m}\n" for m in dati.get('missing_requirements', [])) or "Nav norādīts."}

---

### 💡 Spriedums
**{dati.get('verdict', 'Nav sprieduma.')}**
"""
    with open(fails, "w", encoding="utf-8") as f:
        f.write(parskats.strip())

# ------------------------------------------------------------
# GALVENĀ FUNKCIJA
# ------------------------------------------------------------
def main():
    """Galvenā programma: salīdzina JD ar vairākiem CV un ģenerē rezultātus."""
    print("🚀 AI darbināts CV vērtētājs tiek palaists...\n")

    jd_cels = "sample_inputs/jd.txt"
    jd_texts = nolasit_failu(jd_cels)

    if not jd_texts:
        print("❌ Nav atrasts darba apraksta fails (jd.txt).")
        return

    cv_fails = [f.name for f in Path("sample_inputs").glob("cv*.txt")]

    for cv in cv_fails:
        cv_cels = f"sample_inputs/{cv}"
        cv_texts = nolasit_failu(cv_cels)
        if not cv_texts:
            print(f"⚠️ Izlaiž {cv} — nav datu.")
            continue

        print(f"🔍 Vērtēju {cv}...")

        prompts = izveidot_promptu(jd_texts, cv_texts)
        rezultats = izsaukt_modeli(prompts)

        nosaukums = cv.split(".")[0]
        json_fails = f"outputs/{nosaukums}.json"
        md_fails = f"outputs/{nosaukums}_report.md"

        saglabat_json(rezultats, json_fails)
        genereet_parskatu(rezultats, md_fails)

        print(f"✅ Sagatavots: {json_fails} un {md_fails}\n")

    print("🎯 Visi CV ir novērtēti un rezultāti saglabāti mapē 'outputs'.")

if __name__ == "__main__":
    main()