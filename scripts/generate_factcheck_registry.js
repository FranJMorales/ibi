const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();
const OUTPUT_DIR = path.join(ROOT, "data");
const OUTPUT_FILE = path.join(OUTPUT_DIR, "municipal_factcheck.json");
const COMMUNITIES = [
  "aragon",
  "asturias",
  "castilla-la-mancha",
  "castilla-y-leon",
  "extremadura",
  "galicia",
  "murcia",
];

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function walkMunicipalities() {
  const result = [];
  for (const community of COMMUNITIES) {
    const communityDir = path.join(ROOT, community);
    if (!fs.existsSync(communityDir)) continue;
    for (const province of fs.readdirSync(communityDir, { withFileTypes: true })) {
      if (!province.isDirectory()) continue;
      const provinceDir = path.join(communityDir, province.name);
      for (const town of fs.readdirSync(provinceDir, { withFileTypes: true })) {
        if (!town.isDirectory()) continue;
        const mainIndex = path.join(provinceDir, town.name, "index.html");
        if (fs.existsSync(mainIndex)) {
          result.push(`${community}/${province.name}/${town.name}`);
        }
      }
    }
  }
  return result.sort();
}

function loadExisting() {
  if (!fs.existsSync(OUTPUT_FILE)) return {};
  try {
    return JSON.parse(fs.readFileSync(OUTPUT_FILE, "utf8"));
  } catch {
    return {};
  }
}

function main() {
  ensureDir(OUTPUT_DIR);
  const existing = loadExisting();
  const registry = {};

  for (const slug of walkMunicipalities()) {
    const current = existing[slug] || {};
    registry[slug] = {
      verified: current.verified === true,
      source_title: current.source_title || "",
      source_url: current.source_url || "",
      source_date: current.source_date || "",
      notes: current.notes || "",
      candidate: current.candidate || {},
      values: {
        ibiUrban: current.values?.ibiUrban || "",
        ibiRustic: current.values?.ibiRustic || "",
        paymentPeriod: current.values?.paymentPeriod || "",
        boniFamily: current.values?.boniFamily || "",
        solarBoni: current.values?.solarBoni || "",
        basuraAmount: current.values?.basuraAmount || "",
        basuraPeriod: current.values?.basuraPeriod || "",
        electronicOffice: current.values?.electronicOffice || "",
      },
    };
  }

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(registry, null, 2), "utf8");
  console.log(`factcheck_registry_entries=${Object.keys(registry).length}`);
}

main();
