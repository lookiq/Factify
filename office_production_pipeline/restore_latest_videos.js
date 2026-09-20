const fs = require('fs');
const path = require('path');

const backupDir = path.resolve('temp/output_backup');
const outputDir = path.resolve('output');

if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

// The latest/final version for each unique video
const filesToKeep = [
  'Science_Experiments_Factition_Magic.mp4',       // Latest Factition Science Short
  'Factify_Short_01_ADVENTURE_EDITION.mp4',       // Latest Edition of Short 01 (Mooring Snapback)
  'batch_short_1_1789810084930.mp4',              // Latest Render of Batch Video 1
  'batch_short_2_1789810123642.mp4',              // Latest Render of Batch Video 2
  'batch_short_3_1789810172987.mp4',              // Latest Render of Batch Video 3
  'factition_short_1789804831463.mp4',            // Latest Render of Prototype Video
  'factition_short_1789804831463.json'             // Associated Metadata
];

console.log("Restoring latest file for each video into output/...");

filesToKeep.forEach(file => {
  const src = path.join(backupDir, file);
  const dest = path.join(outputDir, file);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
    const stat = fs.statSync(dest);
    console.log(`✅ Kept latest: ${file} (${(stat.size / (1024 * 1024)).toFixed(2)} MB)`);
  } else {
    console.warn(`File not found in backup: ${src}`);
  }
});

console.log("\nDone! Older duplicate versions were excluded and only the latest file for each video is preserved.");
