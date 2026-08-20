const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();
const REGISTRY_FILE = path.join(ROOT, "data", "municipal_factcheck.json");
const TMP_FILES = ["C:\\tmp\\muni_data.json", "C:\\tmp\\muni_data2.json", "C:\\tmp\\muni_data3.json"];

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function loadMergedTmpData() {
  return TMP_FILES.filter((file) => fs.existsSync(file)).reduce((acc, file) => {
    Object.assign(acc, readJson(file));
    return acc;
  }, {});
}

function main() {
  if (!fs.existsSync(REGISTRY_FILE)) {
    throw new Error("Fact-check registry not found. Run generate_factcheck_registry.js first.");
  }

  const registry = readJson(REGISTRY_FILE);
  const candidates = loadMergedTmpData();
  let imported = 0;

  for (const [slug, candidate] of Object.entries(candidates)) {
    if (!registry[slug]) continue;
    registry[slug].candidate = {
      source_title: candidate.bopRef || "",
      source_url: candidate.sedeElectronica || "",
      extracted_at: new Date().toISOString().slice(0, 10),
      values: {
        ibiUrban: candidate.ibiUrb != null ? `${String(candidate.ibiUrb).replace(".", ",")}%` : "",
        ibiRustic: candidate.ibiRust != null ? `${String(candidate.ibiRust).replace(".", ",")}%` : "",
        paymentPeriod: candidate.periodo ? `${candidate.periodo} 2026` : "",
        boniFamily: candidate.boniFam != null ? `Hasta ${candidate.boniFam}%` : "",
        solarBoni: candidate.boniSolar != null ? `${candidate.boniSolar}%` : "",
        basuraAmount: candidate.basuras != null ? `${candidate.basuras} €/año` : "",
        electronicOffice: candidate.sedeElectronica || "",
      },
    };
    imported++;
  }

  fs.writeFileSync(REGISTRY_FILE, JSON.stringify(registry, null, 2), "utf8");
  console.log(`factcheck_candidates_imported=${imported}`);
}

main();
