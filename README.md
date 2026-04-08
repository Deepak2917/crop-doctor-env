---
title: AI Crop Doctor
emoji: 🌾
colorFrom: green
colorTo: green
sdk: docker
app_port: 7860
pinned: false
tags:
  - openenv
  - agriculture
  - reinforcement-learning
---

# AI Crop Doctor — OpenEnv Environment

## Overview
An OpenEnv-compliant RL environment where an AI agent
acts as an expert agronomist diagnosing crop diseases
on Indian farms.

**Real-world problem:** 600 million Indian farmers lose
30-40% of crops to preventable diseases every year.

## How to use
Select a crop and symptoms in the UI — the AI diagnoses
the disease step by step like a real agronomist.

## Observation Space
| Field            | Type    | Description             |
|------------------|---------|-------------------------|
| crop             | string  | Crop type               |
| region           | string  | Indian state            |
| season           | string  | kharif/rabi/annual      |
| visible_symptoms | list    | Symptoms revealed       |
| questions_asked  | list    | Diagnostic history      |
| steps_remaining  | int     | Steps left              |
| budget_remaining | int     | Budget left             |
| difficulty       | string  | easy/medium/hard        |

## Action Space
ask_more_symptoms, ask_soil_type, ask_recent_rainfall,
prescribe_sulfur_spray, prescribe_neem_oil_spray,
prescribe_copper_oxychloride_spray, prescribe_urea_fertilizer,
prescribe_chlorpyrifos_spray, prescribe_mancozeb_spray,
prescribe_imidacloprid_spray, prescribe_propiconazole_spray,
prescribe_gypsum_fertilizer, prescribe_carbofuran_granules,
prescribe_chlorothalonil_spray, prescribe_metalaxyl_spray

## Reward Function
| Outcome                    | Reward    |
|----------------------------|-----------|
| Correct treatment fast     | up to 1.0 |
| Correct treatment slow     | 0.5-0.9   |
| Good diagnostic question   | +0.10     |
| Minor question             | +0.05     |
| Wrong treatment easy/medium| 0.00      |
| Wrong treatment hard       | -0.20     |

## Tasks
- Easy: 2 symptoms shown, 5 steps max
- Medium: 1 symptom shown, must investigate, 7 steps
- Hard: Confusable disease pair, penalty for wrong, 10 steps

## Baseline Scores
| Task   | Score |
|--------|-------|
| Easy   | 0.67  |
| Medium | 0.67  |
| Hard   | 0.67  |
| Avg    | 0.67  |

## Setup
Set environment variables:
- HF_TOKEN: your Hugging Face token
- API_BASE_URL: https://router.huggingface.co/v1
- MODEL_NAME: Qwen/Qwen2.5-72B-Instruct

Run: python inference.py
Docker: docker build -t crop-doctor . && docker run crop-doctor