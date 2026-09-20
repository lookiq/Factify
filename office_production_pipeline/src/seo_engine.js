/**
 * Advanced YouTube SEO Engine
 * Generates both Offline (File-embedded) and Online (YouTube Algorithm) Metadata
 */

const VIRAL_HASHTAGS = [
  "#shorts",
  "#facts",
  "#mystery",
  "#science",
  "#space",
  "#mindblowing",
  "#didyouknow",
  "#amazingfacts",
  "#factition",
  "#viral",
  "#trending",
  "#deepspace",
  "#unexplained"
];

const CORE_TAGS = [
  "shorts",
  "youtube shorts",
  "facts",
  "interesting facts",
  "mystery",
  "science facts",
  "mind blowing facts",
  "did you know",
  "did you know facts",
  "amazing facts",
  "space mysteries",
  "unexplained mysteries",
  "terrifying discoveries",
  "factition",
  "educational shorts",
  "viral facts",
  "science mysteries",
  "daily facts"
];

/**
 * Generates high-ranking SEO metadata for a topic
 */
function generateSeoMetadata(topicData) {
  const { topic, script, title } = topicData;

  // 1. High-CTR Search-Optimized Title (within 70-85 characters for mobile screens)
  const seoTitle = title.includes('#shorts') ? title : `${title} #shorts`;

  // 2. Extract key topical keywords
  const topicKeywords = topic.toLowerCase().split(/[\s,()]+/).filter(w => w.length > 3);

  // 3. Complete 3-Tier SEO Description for YouTube Algorithm
  const seoDescription = [
    `🔥 ${topic} — Did you know this shocking fact? Watch till the end to discover the mystery!`,
    ``,
    `📌 In this video:`,
    `${script}`,
    ``,
    `🔬 Key Highlights:`,
    `• High-retention science and space exploration facts`,
    `• Authentic scientific discoveries explained simply`,
    `• Comment below your theory on this mystery!`,
    ``,
    `👍 If you loved this Short, smash the LIKE button & SUBSCRIBE for your daily dose of mind-blowing facts!`,
    ``,
    VIRAL_HASHTAGS.join(' ')
  ].join('\n');

  // 4. Broad + Specific + Long-Tail Tags (25+ tags)
  const specificTags = [
    topic.toLowerCase(),
    `${topic.toLowerCase()} facts`,
    `${topic.toLowerCase()} explained`,
    ...topicKeywords.map(k => `${k} mystery`),
    ...topicKeywords.map(k => `${k} facts`)
  ];

  // Merge and deduplicate tags
  const allTags = Array.from(new Set([...specificTags, ...CORE_TAGS])).slice(0, 30);

  // 5. Offline File Metadata (Embedded directly into MP4 container)
  const offlineMetadata = {
    title: seoTitle,
    artist: "Factition",
    album_artist: "Factition Shorts",
    album: "Daily Science Mysteries",
    genre: "Education",
    description: script.slice(0, 250),
    comment: `SEO: ${allTags.slice(0, 10).join(', ')}`,
    keywords: allTags.join(',')
  };

  return {
    title: seoTitle,
    description: seoDescription,
    tags: allTags,
    offlineMetadata,
    category: "27", // Education
    defaultLanguage: "en",
    defaultAudioLanguage: "en"
  };
}

module.exports = {
  generateSeoMetadata,
  VIRAL_HASHTAGS,
  CORE_TAGS
};
