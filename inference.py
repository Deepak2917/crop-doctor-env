import os, random
from openai import OpenAI
from env import CropDoctorEnv

random.seed(42)  # makes grading reproducible

API_BASE_URL = os.getenv("API_BASE_URL",
    "https://router.huggingface.co/v1").strip()
MODEL_NAME   = os.getenv("MODEL_NAME",
    "Qwen/Qwen2.5-72B-Instruct").strip()
API_KEY      = (os.getenv("HF_TOKEN") or
    os.getenv("API_KEY","")).strip()
BENCHMARK    = "crop_doctor"

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
env    = CropDoctorEnv()

ACTIONS = [
    "ask_more_symptoms","ask_soil_type","ask_recent_rainfall",
    "prescribe_sulfur_spray","prescribe_neem_oil_spray",
    "prescribe_copper_oxychloride_spray","prescribe_urea_fertilizer",
    "prescribe_chlorpyrifos_spray","prescribe_mancozeb_spray",
    "prescribe_imidacloprid_spray","prescribe_propiconazole_spray",
    "prescribe_gypsum_fertilizer","prescribe_carbofuran_granules",
    "prescribe_chlorothalonil_spray","prescribe_metalaxyl_spray",
]

SYMPTOM_MAP = {
    "white_powder_on_leaves": "prescribe_sulfur_spray",
    "white_powder":           "prescribe_sulfur_spray",
    "grey_powder":            "prescribe_mancozeb_spray",
    "sticky_residue":         "prescribe_neem_oil_spray",
    "curling_leaves":         "prescribe_neem_oil_spray",
    "distorted_growth":       "prescribe_imidacloprid_spray",
    "brown_water_spots":      "prescribe_copper_oxychloride_spray",
    "tan_lesions":            "prescribe_propiconazole_spray",
    "pale_yellow_leaves":     "prescribe_urea_fertilizer",
    "purple_tint":            "prescribe_gypsum_fertilizer",
    "holes_in_stem":          "prescribe_chlorpyrifos_spray",
    "hollow_stems":           "prescribe_carbofuran_granules",
    "dark_brown_spots":       "prescribe_chlorothalonil_spray",
    "water_soaked_spots":     "prescribe_metalaxyl_spray",
    "white_mold":             "prescribe_metalaxyl_spray",
}

def fallback(obs):
    for sym in obs.visible_symptoms:
        if sym in SYMPTOM_MAP:
            return SYMPTOM_MAP[sym]
    return "ask_more_symptoms"

def get_action(obs) -> str:
    symptoms = ", ".join(obs.visible_symptoms)
    asked    = ", ".join(obs.questions_asked) or "none"
    prompt = f"""You are an expert Indian agronomist.
Crop: {obs.crop} | Region: {obs.region} | Season: {obs.season}
Visible symptoms: {symptoms}
Already asked: {asked}
Steps remaining: {obs.steps_remaining}

Disease guide:
- white_powder_on_leaves → prescribe_sulfur_spray
- grey_powder → prescribe_mancozeb_spray
- sticky_residue or curling_leaves → prescribe_neem_oil_spray
- distorted_growth → prescribe_imidacloprid_spray
- brown_water_spots → prescribe_copper_oxychloride_spray
- tan_lesions → prescribe_propiconazole_spray
- pale_yellow_leaves → prescribe_urea_fertilizer
- purple_tint → prescribe_gypsum_fertilizer
- holes_in_stem or dead_heart → prescribe_chlorpyrifos_spray
- hollow_stems → prescribe_carbofuran_granules
- dark_brown_spots → prescribe_chlorothalonil_spray
- water_soaked_spots or white_mold → prescribe_metalaxyl_spray

RULES:
- If steps remaining is 3 or less you MUST prescribe now
- Reply with ONLY the action name, nothing else

Valid actions:
ask_more_symptoms
ask_soil_type
ask_recent_rainfall
prescribe_sulfur_spray
prescribe_neem_oil_spray
prescribe_copper_oxychloride_spray
prescribe_urea_fertilizer
prescribe_chlorpyrifos_spray
prescribe_mancozeb_spray
prescribe_imidacloprid_spray
prescribe_propiconazole_spray
prescribe_gypsum_fertilizer
prescribe_carbofuran_granules
prescribe_chlorothalonil_spray
prescribe_metalaxyl_spray"""
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role":"user","content":prompt}],
            max_tokens=30,
            temperature=0.0,
        )
        raw = resp.choices[0].message.content.strip().lower()
        raw = raw.replace(" ","_").replace("-","_")
        return raw if raw in ACTIONS else fallback(obs)
    except Exception as e:
        print(f"API error: {e}", flush=True)
        return fallback(obs)

def run_task(difficulty: str) -> float:
    obs     = env.reset(difficulty=difficulty)
    rewards = []
    done    = False
    step_n  = 0

    print(f"[START] task={difficulty} env={BENCHMARK}"
          f" model={MODEL_NAME}", flush=True)

    while not done and step_n < 10:
        action = get_action(obs)
        obs, reward, done, info = env.step(action)
        step_n += 1
        rewards.append(reward.value)
        error_str = info.get("error") or "null"
        print(
            f"[STEP]  step={step_n} action={action}"
            f" reward={reward.value:.2f}"
            f" done={str(done).lower()}"
            f" error={error_str}",
            flush=True,
        )

    grade   = env.grade(rewards) if rewards else 0.0
    grade   = grade if grade is not None else 0.0
    success = grade >= 0.5
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END]   success={str(success).lower()}"
        f" steps={step_n} rewards={rewards_str}",
        flush=True,
    )
    return grade

if __name__ == "__main__":
    scores = {}
    for diff in ["easy","medium","hard"]:
        ep_scores = []
        for ep in range(3):
            try:
                s = run_task(diff)
                ep_scores.append(s)
            except Exception as e:
                print(f"Episode error: {e}", flush=True)
                print(f"[END]   success=false"
                      f" steps=0 rewards=0.00", flush=True)
                ep_scores.append(0.0)
        avg = round(sum(ep_scores)/len(ep_scores), 2)
        scores[diff] = avg
        print(f"Task {diff}: episodes={ep_scores}"
              f" avg={avg}", flush=True)

    final = round(sum(scores.values())/3, 2)
    print(f"\nFinal scores: {scores}", flush=True)
    print(f"Average: {final}", flush=True)