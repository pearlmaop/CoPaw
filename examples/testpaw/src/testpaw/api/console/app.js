async function api(path, method = "GET", body) {
  const init = { method, headers: {} };
  if (body !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  const resp = await fetch(path, init);
  return resp.json();
}

function renderProviders(providers) {
  const root = document.getElementById("providers");
  root.innerHTML = "";
  providers.forEach((p) => {
    const div = document.createElement("div");
    div.className = "item";
    div.innerHTML = `
      <strong>${p.provider_id}</strong><br>
      model: ${p.model || ""}<br>
      active: ${String(p.active)}
      <div class="inline-actions">
        <button class="small" data-provider="${p.provider_id}">设为激活</button>
      </div>
    `;
    div.querySelector("button").addEventListener("click", async () => {
      await api("/providers/activate", "POST", { provider_id: p.provider_id });
      await loadProviders();
    });
    root.appendChild(div);
  });
}

function renderSkills(skills) {
  const root = document.getElementById("skills");
  root.innerHTML = "";
  skills.forEach((s) => {
    const div = document.createElement("div");
    div.className = "item";
    div.innerHTML = `
      <strong>${s.skill_id}</strong><br>
      ${s.description}<br>
      enabled: ${String(s.enabled)}
      <div class="inline-actions">
        <button class="small" data-skill="${s.skill_id}" data-enabled="${s.enabled}">${s.enabled ? "禁用" : "启用"}</button>
      </div>
    `;
    div.querySelector("button").addEventListener("click", async (e) => {
      const btn = e.currentTarget;
      const enabled = btn.getAttribute("data-enabled") !== "true";
      await api(`/skills/${s.skill_id}/enable`, "POST", { enabled });
      await loadSkills();
    });
    root.appendChild(div);
  });
}

async function loadProviders() {
  const data = await api("/providers");
  renderProviders(data.providers || []);
}

async function loadSkills() {
  const data = await api("/skills");
  renderSkills(data.skills || []);
}

document.getElementById("providerForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.currentTarget);
  const provider_id = form.get("provider_id");
  await api(`/providers/${provider_id}/config`, "POST", {
    model: form.get("model") || null,
    base_url: form.get("base_url") || null,
    api_key: form.get("api_key") || null,
  });
  await loadProviders();
});

document.getElementById("skillRunForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.currentTarget);
  const skill_id = form.get("skill_id");
  const text = form.get("text") || "";
  const data = await api(`/skills/${skill_id}/run`, "POST", { text });
  document.getElementById("skillOutput").textContent = JSON.stringify(data, null, 2);
});

document.getElementById("chatForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.currentTarget);
  const data = await api("/chat", "POST", {
    text: form.get("text") || "",
    agent_id: form.get("agent_id") || "default",
    session_id: "console-session",
    user_id: "console-user",
    channel: "console",
  });
  document.getElementById("chatOutput").textContent = JSON.stringify(data, null, 2);
});

loadProviders();
loadSkills();
