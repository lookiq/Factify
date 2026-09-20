# Factition (@Factitionn) YouTube Automation Specification

This document bridges the YouTube Shorts automation pipeline with the exact content format, tone, and viral topics of **Factition** ([@Factitionn](https://www.youtube.com/@Factitionn)).

---

## 1. Channel Profile & Niche
- **Reference Channel**: [Factition (@Factitionn)](https://www.youtube.com/@Factitionn) (428K+ subscribers)
- **Primary Niche**: High-Curiosity Science, Extreme Engineering, Dangerous Hazards, Bizarre Machines, Unexplained Phenomena
- **Video Format**: Vertical Shorts (9:16, 1080x1920, 40–55 seconds)
- **Target Retention Goal**: >100% (using continuous loop hook & rapid pacing)

---

## 2. Dynamic Rule Enforcement (Flexible Mode)
Not every video has to satisfy all 3 rules. Rules apply dynamically based on the content tier:

1. **Extreme Viral Tier (High-Danger / Lethal Workplace / Shock Science)**:
   - **Enforces 3/3 Rules Strictly**: Extreme shock hook + violent action footage + global appeal.
   - *Examples*: Ship Mooring Snapback, 500,000 Volts Linemen, Snake Venom Immunity.
2. **Curiosity & Science Mystery Tier (Space / Biology Quirks / What-Ifs)**:
   - **Enforces 2/3 Rules (Flexible Footage)**: High curiosity + global appeal, but footage can be smooth ambient/macro/space motion rather than violent action.
   - *Examples*: Why Bats Hang Upside Down, What If Earth Stopped Spinning.
3. **Odd Technology & Engineering Tier (Strange Machines / Construction Secrets)**:
   - **Enforces 2/3 Rules (Flexible Hook)**: Real visual machine appeal + global curiosity, without needing extreme life-or-death shock.
   - *Examples*: China's Walking Buildings, Polyurethane Highway Injections, AI Laser Weed Tractors.

---

## 3. Voice & Tone Configurations
Configured for **`@andresaya/edge-tts`** (100% Free, zero latency, word boundaries included):

```javascript
// English (Deep, authoritative, documentary narrator):
{
  voice: 'en-US-ChristopherNeural',
  rate: '+5%',
  pitch: '-2Hz'
}

// Hindi (Original Factition Style - fast, dramatic South Asian storytelling):
{
  voice: 'hi-IN-MadhurNeural',
  rate: '+6%',
  pitch: '-1Hz'
}

// Bengali (Fast, engaging narration):
{
  voice: 'bn-BD-PradeepNeural',
  rate: '+5%',
  pitch: '-1Hz'
}
```

---

## 3. Script Structure & AI Prompt Formula (Gemini API)

When generating a script, use this exact prompt:

```text
You are the master scriptwriter for a viral YouTube Shorts fact channel like @Factitionn.
Write a high-retention 45-second script on the topic: {TOPIC}

RULES:
1. HOOK (0-3s): Start with an irresistible curiosity gap or shock statement. Never say "Hello guys" or "Welcome back".
2. STORY (3-40s): Short, punchy sentences (max 10-12 words per sentence). Break into 4 visual scenes. Explain the mechanism with zero fluff.
3. PAYOFF (40-48s): Reveal the surprising conclusion.
4. LOOP CTA (48-50s): End with a seamless transition that loops back to the start or asks a 1-word opinion question.
5. FORMAT: Provide the voiceover script plain text, followed by 4 B-roll search keywords for Pexels.
```

---

## 4. Topics Database
See [`topics.json`](./topics.json) for:
- 10+ ready-to-render curated viral topics with hooks, core facts, and Pexels b-roll keywords.
- Viral hook templates and subtitle styling parameters.
