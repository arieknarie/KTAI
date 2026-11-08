// Snel achter elkaar een andere keuze voor hetzelfde gezicht: de laatste keuze moet in labels.csv staan, ook als de
// opslagverzoeken elkaar inhalen (app.js stuurt ze daarom één voor één, in de volgorde van de keuzes).
import { connect, check, sleep, rows } from "./lib.mjs";

const page = await connect();
await page.fresh();
const item = Math.max(0, await page.find(`i.kind !== "track"`));
await page.show(item);
const face = await page.js(`state.data.items[${item}].faces[0].face`);
const sequence = ["unknown", "no_face", "other", "unknown", "other", "no_face", "unknown", "other", "no_face", "other"];
// direct via save(): de rem van 0,3 seconde in choose() zou zulke snelle keuzes anders tegenhouden
await page.js(`${JSON.stringify(sequence)}.forEach(label => save([labelRow(state.data.items[${item}], state.data.items[${item}].faces[0], label)])); saving`);
await sleep(500);
const found = rows().filter(r => r.face === face);
check("10 snelle wijzigingen: de laatste keuze staat in labels.csv", found.length === 1 && found[0].label === "other", JSON.stringify(found));
page.close();
