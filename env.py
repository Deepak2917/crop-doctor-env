import json, random
from pydantic import BaseModel

with open("diseases.json") as f:
    DISEASES = json.load(f)

CONFUSABLE_PAIRS = [
    ("powdery_mildew", "false_mildew"),
    ("whitefly", "aphid_attack"),
    ("bacterial_blight", "leaf_scald"),
    ("nitrogen_deficiency", "sulfur_deficiency"),
    ("stem_borer", "root_borer"),
    ("early_blight", "late_blight"),
]

class CropObservation(BaseModel):
    crop: str
    region: str
    season: str
    visible_symptoms: list
    questions_asked: list
    steps_remaining: int
    budget_remaining: int
    difficulty: str

class CropAction(BaseModel):
    action: str

class CropReward(BaseModel):
    value: float
    reason: str

VALID_ACTIONS = [
    "ask_more_symptoms",
    "ask_soil_type",
    "ask_recent_rainfall",
    "prescribe_sulfur_spray",
    "prescribe_neem_oil_spray",
    "prescribe_copper_oxychloride_spray",
    "prescribe_urea_fertilizer",
    "prescribe_chlorpyrifos_spray",
    "prescribe_mancozeb_spray",
    "prescribe_imidacloprid_spray",
    "prescribe_propiconazole_spray",
    "prescribe_gypsum_fertilizer",
    "prescribe_carbofuran_granules",
    "prescribe_chlorothalonil_spray",
    "prescribe_metalaxyl_spray",
]

class CropDoctorEnv:

    def reset(self, difficulty: str = "easy") -> CropObservation:
        self.difficulty = difficulty
        self.steps_taken = 0
        self.questions_asked = []
        self.done = False
        self.last_action_error = None
        self.budget = 10
        self.max_steps = {
            "easy": 5, "medium": 7, "hard": 10
        }[difficulty]

        if difficulty == "hard":
            pair = random.choice(CONFUSABLE_PAIRS)
            key  = random.choice(list(pair))
        else:
            key = random.choice(list(DISEASES.keys()))

        self.disease           = DISEASES[key]
        self.disease_key       = key
        self.correct_treatment = self.disease["treatment"]

        if difficulty == "easy":
            self.visible_symptoms = list(
                self.disease["symptoms"][:2]
            )
        else:
            self.visible_symptoms = [self.disease["symptoms"][0]]

        return self._obs()

    def state(self) -> CropObservation:
        return self._obs()

    def _obs(self) -> CropObservation:
        return CropObservation(
            crop=self.disease["crop"],
            region=self.disease["region"],
            season=self.disease["season"],
            visible_symptoms=list(self.visible_symptoms),
            questions_asked=list(self.questions_asked),
            steps_remaining=self.max_steps - self.steps_taken,
            budget_remaining=self.budget,
            difficulty=self.difficulty,
        )

    def step(self, action: str):
        self.last_action_error = None

        if action not in VALID_ACTIONS:
            self.last_action_error = f"invalid_action:{action}"
            reward = CropReward(value=0.0, reason="invalid action")
            return self._obs(), reward, self.done, {
                "error": self.last_action_error
            }

        self.steps_taken += 1
        self.budget      -= 1
        reward_val        = 0.0
        reason            = ""

        if action == "ask_more_symptoms":
            hidden = [s for s in self.disease["symptoms"]
                      if s not in self.visible_symptoms]
            if hidden:
                self.visible_symptoms.append(hidden[0])
            self.questions_asked.append("asked_symptoms")
            reward_val = 0.1
            reason     = "good diagnostic question"

        elif action in ("ask_soil_type", "ask_recent_rainfall"):
            self.questions_asked.append(action)
            reward_val = 0.05
            reason     = "minor diagnostic question"

        elif action.startswith("prescribe_"):
            treatment = action.replace("prescribe_", "")
            if treatment == self.correct_treatment:
                steps_ratio  = self.steps_taken / self.max_steps
                budget_bonus = self.budget / 10
                eff = 1.0 - (steps_ratio * 0.2) + (budget_bonus * 0.1)
                reward_val = round(min(1.0, max(0.5, eff)), 2)
                reason     = "correct treatment"
            else:
                reward_val = -0.2 if self.difficulty == "hard" else 0.0
                reason     = "wrong treatment"
            self.done = True

        if self.steps_taken >= self.max_steps:
            self.done = True

        reward = CropReward(value=reward_val, reason=reason)
        info   = {
            "error":             self.last_action_error,
            "steps_taken":       self.steps_taken,
            "correct_treatment": self.correct_treatment,
            "difficulty":        self.difficulty,
            "budget_remaining":  self.budget,
        }
        return self._obs(), reward, self.done, info

    def grade(self, task_rewards: list) -> float:
        if not task_rewards:
            return 0.0
        last  = task_rewards[-1]
        total = sum(task_rewards)
        if last >= 0.5:
            return round(min(1.0, total), 2)
        if last < 0:
            return 0.0
        return round(min(0.3, total * 0.5), 2)