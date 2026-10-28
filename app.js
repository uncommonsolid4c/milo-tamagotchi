async function j(method, path, body) {
  const r = await fetch(path, {
    method,
    headers: {"Content-Type": "application/json"},
    body: body ? JSON.stringify(body) : undefined,
  });
  const d = await r.json();
  if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
  return d;
}
function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function when(iso) {
  try { return new Date(iso).toLocaleString(); } catch (e) { return iso; }
}
function renderPet(pet) {
  document.getElementById("name").textContent = pet.name;
  document.getElementById("day").textContent = pet.dayLabel;
  document.getElementById("stage").textContent = pet.stageLabel;
  document.getElementById("mood").textContent = pet.sick ? "sick" : pet.mood;
  document.getElementById("health").textContent = pet.health;
  document.getElementById("happiness").textContent = pet.happiness;
  document.getElementById("hunger").textContent = pet.hunger;
  document.getElementById("energy").textContent = pet.energy;
  document.getElementById("poops").textContent = pet.poops;
  document.getElementById("sleeping").textContent = pet.sleeping ? "yes 💤" : "no";
  document.getElementById("sleepBtn").textContent = pet.sleeping ? "☀️ Wake up" : "💤 Sleep";
}
function renderDiary(entries) {
  document.getElementById("diary").innerHTML = entries.map(e =>
    "<div><span class=\"who\">" + esc(e.author) + "</span> <span class=\"when\">" + when(e.createdAt) +
    "</span><br>" + esc(e.body) + "</div>").join("") || "<div>No entries yet.</div>";
}
function renderLog(log) {
  document.getElementById("log").innerHTML = log.slice(0, 30).map(e =>
    "<div><span class=\"when\">" + when(e.createdAt) + "</span> " + esc(e.label) + "</div>").join("");
}
async function refresh() {
  const s = await j("GET", "api/state");
  renderPet(s.pet);
  renderLog(s.recentLog);
  const d = await j("GET", "api/diary");
  renderDiary(d.entries);
}
function say(msg) { document.getElementById("msg").textContent = msg; }
document.querySelectorAll("[data-feed]").forEach(b => b.addEventListener("click", async () => {
  try { const d = await j("POST", "api/feed", {food: b.dataset.feed}); renderPet(d.pet); say(d.message); refresh(); }
  catch (e) { say("Error: " + e.message); }
}));
document.getElementById("cleanBtn").addEventListener("click", async () => {
  try { const d = await j("POST", "api/clean", {}); renderPet(d.pet); say(d.message); refresh(); }
  catch (e) { say("Error: " + e.message); }
});
document.getElementById("sleepBtn").addEventListener("click", async () => {
  try { const d = await j("POST", "api/sleep", {}); renderPet(d.pet); say(d.pet.sleeping ? "Milo went to sleep 💤" : "Milo woke up ☀️"); refresh(); }
  catch (e) { say("Error: " + e.message); }
});
document.querySelectorAll("[data-play]").forEach(b => b.addEventListener("click", async () => {
  try {
    const d = await j("POST", "api/play", {choice: b.dataset.play});
    renderPet(d.pet);
    say("You: " + d.you + " · Milo: " + d.server + " · " + d.outcome + "!");
    refresh();
  } catch (e) { say("Error: " + e.message); }
}));
document.getElementById("diaryBtn").addEventListener("click", async () => {
  const ta = document.getElementById("diaryText");
  const body = ta.value.trim();
  if (!body) return;
  try { await j("POST", "api/diary", {author: "user", body}); ta.value = ""; say("Diary entry added."); refresh(); }
  catch (e) { say("Error: " + e.message); }
});
refresh();
