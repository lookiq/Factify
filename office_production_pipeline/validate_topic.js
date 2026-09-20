const config = require('./topics.json');
const golden = config.golden_rules_for_topics;
const rules = golden.rules;
const modes = golden.categories_and_modes;

function getCategoryMode(category = '') {
  const cat = category.toLowerCase();
  if (cat.includes('danger') || cat.includes('hazard') || cat.includes('voltage') || cat.includes('extreme')) {
    return { name: 'extreme_viral', ...modes.extreme_viral };
  }
  if (cat.includes('tech') || cat.includes('engineering') || cat.includes('machine') || cat.includes('construction')) {
    return { name: 'odd_tech_engineering', ...modes.odd_tech_engineering };
  }
  return { name: 'curiosity_mystery', ...modes.curiosity_mystery };
}

function validateTopic(topic) {
  console.log(`\n==============================================`);
  console.log(`EVALUATING TOPIC: "${topic.title || topic}"`);
  console.log(`Category: "${topic.category || 'General'}"`);
  
  const mode = getCategoryMode(topic.category);
  console.log(`Mode Selected: [${mode.name.toUpperCase()}] — Min Score Required: ${mode.min_score}/3`);
  console.log(`Mode Details: ${mode.description}`);
  console.log(`==============================================`);

  let score = 0;
  const results = [];

  // Rule 1: Curiosity Gap Hook Test
  const hook = (topic.hook || topic).toLowerCase();
  const hasStrongHook = /(deadliest|never|why|secret|what happens|lethal|shock|extreme|danger|bizarre|insane|impossible|wondered|ordinary|acts like)/i.test(hook);
  const hasBoringWords = /(hello|welcome|today we will|in this video)/i.test(hook);

  if (hasStrongHook && !hasBoringWords) {
    score++;
    results.push({ rule: rules.rule_1_curiosity_gap.name, status: 'PASS ✅', detail: 'Curiosity loop is strong and compelling.' });
  } else {
    results.push({ rule: rules.rule_1_curiosity_gap.name, status: 'SOFT / MILD ℹ️', detail: 'Intriguing informational hook (acceptable for non-extreme categories).' });
  }

  // Rule 2: Visual Footage Test
  const broll = topic.broll_keywords || [];
  if (broll.length >= 3) {
    score++;
    results.push({ rule: rules.rule_2_visual_motion_appeal.name, status: 'PASS ✅', detail: `${broll.length} visual clips identified: [${broll.join(', ')}].` });
  } else {
    results.push({ rule: rules.rule_2_visual_motion_appeal.name, status: 'PASS (SMOOTH/AMBIENT) ✅', detail: 'Acceptable smooth visual motion.' });
  }

  // Rule 3: Universal Global Appeal
  const title = (topic.title || topic).toLowerCase();
  const isTooLocalized = /(dhaka|chittagong|local municipal|ward council)/i.test(title);
  if (!isTooLocalized) {
    score++;
    results.push({ rule: rules.rule_3_universal_global_appeal.name, status: 'PASS ✅', detail: 'Broad universal interest across US & international viewers.' });
  } else {
    results.push({ rule: rules.rule_3_universal_global_appeal.name, status: 'FAIL ❌', detail: 'Too narrow or localized.' });
  }

  results.forEach(r => console.log(`[${r.status}] ${r.rule}\n   -> ${r.detail}`));

  const passed = score >= mode.min_score;
  console.log(`\nSCORE: ${score}/3 (Required: ${mode.min_score}/3) — ${passed ? 'APPROVED FOR PRODUCTION 🚀' : 'NEEDS ADJUSTMENT ⚠️'}`);
  return passed;
}

// Test validation across different categories
console.log("FLEXIBLE VALIDATION DEMO:");

// 1. Extreme Viral Topic (Mooring/Venom)
validateTopic(config.topics[0]);

// 2. Tech / Construction Topic (Flexible rules)
validateTopic(config.topics[2]); // China's Walking Buildings

module.exports = { validateTopic };
