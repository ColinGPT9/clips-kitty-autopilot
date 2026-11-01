"use strict";
const $ = (id) => document.getElementById(id);
let state, refreshing = false, toastTimer;
function node(tag, text, cls) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; }
function toast(message) { $("toast").textContent = message; $("toast").hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { $("toast").hidden = true; }, 8500); }
async function api(path, body, method = "POST") {
  const response = await fetch(path, {method, credentials: "same-origin", headers: {"Content-Type": "application/json", "X-Autopilot-Action": "1"}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
  const data = await response.json();
  if (!response.ok) throw new Error(Array.isArray(data.detail) ? data.detail.map(e => `${e.field}: ${e.message}`).join("; ") : data.detail || "The request failed. Try again.");
  return data;
}
function button(text, action, cls = "secondary") { const b = node("button", text, cls); b.type = "button"; b.addEventListener("click", async () => { b.disabled = true; try { await action(); await refresh(); } catch (e) { toast(e.message); } finally { b.disabled = false; } }); return b; }
function external(text, url, cls) { const a = node("a", text, cls); try { const u = new URL(url); if (u.protocol === "https:") { a.href = u.href; a.target = "_blank"; a.rel = "noopener noreferrer"; } } catch {} return a; }
function empty(container, title, detail) { const item = node("div", undefined, "empty"); item.append(node("strong", title), node("p", detail)); container.append(item); }
function openDamageControl() { $("damage-dialog").showModal(); }
const platformNames = {instagram:"Instagram",tiktok:"TikTok",youtube:"YouTube",facebook:"Facebook",x:"X",threads:"Threads",linkedin:"LinkedIn",linkedin_pages:"LinkedIn Page",pinterest:"Pinterest",bluesky:"Bluesky",wooptest:"WoopSocial Test"};
function selectedProfiles() { return state.settings.selected_destinations || (state.settings.instagram_id ? [{id:state.settings.instagram_id,platform:"instagram",username:state.settings.instagram_username}] : []); }
function profileText(accounts) { return accounts.map(a=>`${platformNames[a.platform] || a.platform} @${a.username || a.id || a.account_id}`).join(" · "); }
function date(value) { if (!value) return "—"; return new Date(typeof value === "number" ? value * 1000 : value).toLocaleString([], {month:"short",day:"numeric",hour:"numeric",minute:"2-digit", timeZone: state.settings.timezone}); }
function renderWatches() {
  const root = $("watches"); root.replaceChildren();
  if (!state.watches.length) return empty(root, "Every great moment starts with a community.", "Watch a Twitch channel to start finding the viewer clips that reach your target.");
  for (const w of state.watches) {
    const card = node("article", undefined, "watch-card"), info = node("div"), actions = node("div", undefined, "watch-actions");
    info.append(external(`twitch.tv/${w.login} ↗`, `https://www.twitch.tv/${w.login}`));
    info.append(node("p", `${w.enabled ? "Watching" : "Paused"} · Twitch clips · ${w.mode === "auto" ? "Automatic" : "Ask first"} · Gaming + ${w.options.captions ? "captions" : "no captions"}`));
    info.append(node("p", w.last_polled ? `Last checked ${date(w.last_polled)}` : "First check pending"));
    if (w.error) info.append(node("p", w.error, "error"));
    const label = node("label", "View target"), input = node("input"); input.type = "number"; input.min = "0"; input.max = "10000000"; input.value = w.min_views; input.setAttribute("aria-label", `View target for ${w.login}`); label.append(input);
    actions.append(label, button("Save", async () => { await api(`/api/watches/${w.id}`, {min_views: Number(input.value)}, "PATCH"); toast("View target saved."); }), button("Check now", () => api(`/api/watches/${w.id}/check`, {})), button(w.enabled ? "Pause" : "Resume", () => api(`/api/watches/${w.id}`, {enabled: !w.enabled}, "PATCH")));
    const mode = node("select"); mode.setAttribute("aria-label", `Publishing mode for ${w.login}`); for (const [value, text] of [["ask","Ask first"],["auto","Automatic"]]) { const o = node("option", text); o.value = value; mode.append(o); } mode.value = w.mode;
    mode.addEventListener("change", async () => { try { await api(`/api/watches/${w.id}`, {mode: mode.value}, "PATCH"); await refresh(); } catch(e) { mode.value = w.mode; toast(e.message); } }); actions.append(mode);
    card.append(info, actions); root.append(card);
  }
}
const names = {baseline:"Earlier clip",queued:"Queued",waiting:"Waiting for room",rendering:"Making it vertical",review:"Ready to review",sending:"Scheduling",scheduled:"Scheduled",published:"Published",denied:"Denied",error:"Needs attention",needs_check:"Check WoopSocial",overlap:"Similar moment skipped"};
function renderClips() {
  const root = $("clip-list"), filter = $("clip-filter").value; root.replaceChildren();
  const clips = state.clips.filter(c => filter === "all" || (filter === "baseline" ? c.state === "baseline" : !["baseline","denied","overlap","published"].includes(c.state)));
  if (!clips.length) return empty(root, filter === "baseline" ? "Earlier moments will appear here." : "Waiting for the next good moment.", "Clips below your target are checked again on the next poll.");
  for (const c of clips) {
    const card = node("article", undefined, "clip-card"), cover = node("div", undefined, "clip-cover"), body = node("div", undefined, "clip-body");
    cover.append(node("span", names[c.state] || c.state, "pill"));
    if (c.media_url) cover.append(button("▶ Preview", () => { $("preview-title").textContent = c.title; $("preview-video").src = c.media_url; $("preview-dialog").showModal(); }, "play"));
    body.append(node("h3", c.title), node("p", `${Number(c.views).toLocaleString()} views · Clipped by ${c.creator}`), node("p", c.reached_at ? `Reached target ${date(c.reached_at)}` : "Already above target at first check"));
    if(c.duration) body.append(node("p", `${c.duration.toFixed(1)}s · Whole clip · 1080 × 1920 · Gaming`));
    if(c.error) body.append(node("p", c.error, "error"));
    body.append(external("Original Twitch clip ↗", c.source_url, "source"));
    const actions = node("div", undefined, "buttons");
    if(c.state === "review") {
      const profiles = selectedProfiles(), account_ids = profiles.map(a=>a.id), destination_revision = state.settings.destination_revision;
      const damage = node("button", "Damage Control", "secondary");
      damage.type = "button"; damage.addEventListener("click", openDamageControl);
      body.append(node("p", profiles.length ? `Destinations: ${profileText(profiles)}` : "Choose publishing profiles in Settings.", "caption"));
      const text = profiles.length === 1 ? `Schedule to ${profiles[0].platform === "instagram" ? "" : (platformNames[profiles[0].platform]+" ")}@${profiles[0].username || profiles[0].id}` : profiles.length ? `Schedule to ${profiles.length} profiles` : "Select profiles in Settings";
      actions.append(button(text, () => api(`/api/clips/${c.id}/approve`, {account_ids,destination_revision}), "primary"), damage);
    }
    if(["baseline","denied","error"].includes(c.state)) actions.append(button(c.state === "error" ? "Retry processing" : "Clip this", () => api(`/api/clips/${c.id}/queue`, {})));
    if(["baseline","waiting","queued","review","error"].includes(c.state)) actions.append(button("Deny", () => api(`/api/clips/${c.id}/deny`, {}), "ghost"));
    body.append(actions); card.append(cover, body); root.append(card);
  }
}
function renderPosts() {
  const root = $("posts"); root.replaceChildren();
  if (!state.posts.length) return empty(root, "Your schedule is clear.", "Ready clips are scheduled to your selected profiles after your approval.");
  for(const p of state.posts) {
    const row = node("div", undefined, "post-row"), title = node("div"), when = node("div", undefined, "when");
    const accounts = p.destinations?.length ? p.destinations : [{platform:"instagram",username:p.account_username}];
    title.append(node("strong", p.title), node("p", `${profileText(accounts)} · ${names[p.state] || p.state}`));
    for(const delivery of p.deliveries || []) { const line = node("p", `${profileText([delivery])}: ${delivery.state}`); if(delivery.post_url) line.append(document.createTextNode(" · "),external("View post ↗",delivery.post_url)); if(delivery.error) line.append(document.createTextNode(` · ${delivery.error}`)); title.append(line); }
    when.append(node("div", date(p.scheduled_for)), node("p", state.settings.timezone)); if (p.post_url && !p.deliveries?.length) when.append(external("View published post ↗", p.post_url)); row.append(title, when); root.append(row);
  }
}
function renderEvents() { const root = $("events"); root.replaceChildren(); if(!state.events.length) return empty(root,"Nothing happening just yet.","Connect your accounts and add your first channel."); for(const e of state.events) { const row = node("div",undefined,"event"); const time = node("time",date(e.at)); row.append(time,node("span",e.message)); root.append(row); } }
async function refresh() {
  if (refreshing) return; refreshing = true;
  try {
    state = await api("/api/status", undefined, "GET"); const s = state.settings;
    $("status-label").textContent = s.enabled ? "Watching for the next moment" : "Watching is paused"; $("status-dot").classList.toggle("on",s.enabled); $("toggle").textContent = s.enabled ? "Pause watching" : "Start watching"; $("destination").textContent = selectedProfiles().length ? profileText(selectedProfiles()) : "Choose publishing profiles in Settings";
    for(const key of ["review","scheduled","published"]) $("count-"+key).textContent = state.counts[key]; $("count-pending").replaceChildren(document.createTextNode(state.counts.pending+" "),node("small",`/ ${s.max_pending}`));
    $("schedule-policy").textContent = `${s.per_day} per day · ${s.gap_hours} hour${s.gap_hours === 1 ? "" : "s"} apart`;
    if(!$("watches").contains(document.activeElement)) renderWatches(); renderClips(); renderPosts(); renderEvents();
  } catch(e) { $("status-label").textContent = "Connection needs attention"; toast(e.message); } finally { refreshing = false; }
}
function fillAccounts(accounts) {
  const root = $("destinations"); root.replaceChildren(); const chosen = new Set(selectedProfiles().map(a=>a.id));
  for(const a of accounts.filter(a=>platformNames[a.platform])) {
    const row = node("div",undefined,"account-choice"), label = node("label",undefined,"check"), check = node("input");
    check.type="checkbox"; check.dataset.accountId=a.id; check.checked=chosen.has(a.id); check.setAttribute("aria-label",`Select ${profileText([a])}`);
    label.append(check,document.createTextNode(profileText([a]))); row.append(label);
    const fields=node("div",undefined,"account-options"); fields.hidden=!check.checked;
    const current=state.settings.destination_options?.[a.id] || {};
    function field(key,title,choices) { const label=node("label",title), input=node(choices ? "select" : "input"); input.dataset.option=key; if(choices){for(const [value,text] of choices){const o=node("option",text);o.value=value;input.append(o);}} else input.type="text"; input.value=current[key] || (choices ? choices[0][0] : ""); label.append(input);fields.append(label);return input; }
    if(a.platform==="pinterest") { const input=field("pinterestBoardId","Pinterest board ID");input.maxLength=128; }
    if(a.platform==="youtube") field("privacy","YouTube visibility",[["public","Public"],["unlisted","Unlisted"],["private","Private"]]);
    if(a.platform==="tiktok") {
      field("privacyLevel","TikTok visibility",[["PUBLIC_TO_EVERYONE","Public"],["MUTUAL_FOLLOW_FRIENDS","Friends"],["FOLLOWER_OF_CREATOR","Followers"],["SELF_ONLY","Private"]]);
      for(const [key,text] of [["isYourBrand","Promotes my own brand"],["isBrandedContent","Paid partnership"]]) { const label=node("label",undefined,"check"), input=node("input");input.type="checkbox";input.dataset.option=key;input.checked=current[key]===true;label.append(input,document.createTextNode(text));fields.append(label); }
    }
    check.addEventListener("change",()=>{fields.hidden=!check.checked;});row.append(fields);root.append(row);
  }
  if(!root.children.length) root.append(node("p","Refresh connections to load your available profiles.","caption"));
}
function fillSettings() { const form = $("settings-form"); for(const key of ["twitch_client_id","per_day","max_pending","gap_hours","day_start","timezone"]) form.elements[key].value = state.settings[key]; form.elements.woop_key.value = ""; $("twitch-status").textContent = state.connections.twitch ? `Connected @${state.connections.twitch_login}` : "Not connected"; $("woop-status").textContent = state.connections.woopsocial ? "API key saved. Select the exact profiles these clips should reach." : "Add your WoopSocial key to load connected profiles."; fillAccounts(state.settings.accounts); }
async function saveSettings() { const f = $("settings-form").elements, body = {}; for(const key of ["twitch_client_id","day_start","timezone"]) body[key]=f[key].value.trim(); for(const key of ["per_day","max_pending","gap_hours"]) body[key]=Number(f[key].value); if(f.woop_key.value.trim()) body.woop_key=f.woop_key.value.trim(); await api("/api/settings",body); f.woop_key.value=""; }
$("settings-open").addEventListener("click",()=>{if(!state)return; fillSettings(); $("settings-dialog").showModal();});
$("add-open").addEventListener("click",()=>$("watch-dialog").showModal());
$("damage-open").addEventListener("click",openDamageControl);
document.querySelectorAll("[data-close]").forEach(b=>b.addEventListener("click",()=>$(b.dataset.close).close()));
$("preview-dialog").addEventListener("close",()=>{$("preview-video").pause(); $("preview-video").removeAttribute("src"); $("preview-video").load();});
$("clip-filter").addEventListener("change",()=>state&&renderClips());
$("toggle").addEventListener("click",async()=>{ if(!state)return; try{await api("/api/automation",{enabled:!state.settings.enabled});await refresh();}catch(e){toast(e.message);}});
$("settings-form").addEventListener("submit",async e=>{e.preventDefault();try{await saveSettings();const account_ids=[],options={};for(const row of $("destinations").children){const check=row.querySelector('[data-account-id]');if(!check?.checked)continue;account_ids.push(check.dataset.accountId);const mine={};for(const input of row.querySelectorAll('[data-option]'))mine[input.dataset.option]=input.type==="checkbox"?input.checked:input.value.trim();if(Object.keys(mine).length)options[check.dataset.accountId]=mine;}await api("/api/destinations",{account_ids,options});await refresh();$("settings-dialog").close();toast("Settings saved.");}catch(error){toast(error.message);}});
async function refreshConnections(project_id="") {const data = await api("/api/connections",{project_id});await refresh();fillAccounts(data.accounts);$("project").replaceChildren();for(const p of data.projects){const o=node("option",p.name);o.value=p.id;$("project").append(o);}$("project").value=state.settings.woop_project_id;$("project-label").hidden=data.projects.length<2;$("woop-status").textContent = data.accounts.length ? "Select the profiles to publish to, then save settings. Other profiles stay unselected." : "Choose a project or connect profiles in WoopSocial first.";}
$("woop-refresh").addEventListener("click",async()=>{try{await saveSettings();await refreshConnections();}catch(e){toast(e.message);}});
$("project").addEventListener("change",async()=>{try{await refreshConnections($("project").value);}catch(e){toast(e.message);}});
$("watch-form").addEventListener("submit",async e=>{e.preventDefault();const f=e.target.elements;try{await api("/api/watches",{login:f.login.value.trim(),min_views:Number(f.min_views.value),lookback_days:Number(f.lookback_days.value),mode:f.mode.value,backfill:f.backfill.checked,options:{captions:f.captions.checked,detect_camera:true}});$("watch-dialog").close();await refresh();toast("Channel added.");}catch(error){toast(error.message);}});
$("twitch-connect").addEventListener("click",async()=>{
  try {await saveSettings();const flow=await api("/api/twitch/start",{});const box=$("twitch-code");box.replaceChildren(node("strong",`Enter code ${flow.user_code} at `),external("Twitch Activate ↗",flow.verification_uri));box.hidden=false;
    const poll=async()=>{try{const result=await api("/api/twitch/poll",{flow_id:flow.flow_id});if(result.pending)setTimeout(poll,Math.max(5,flow.interval)*1000);else{box.hidden=true;await refresh();$("twitch-status").textContent=`Connected @${result.login}`;toast("Twitch connected.");}}catch(e){toast(e.message);}};setTimeout(poll,Math.max(5,flow.interval)*1000);
  } catch(e){toast(e.message);}
});
refresh();setInterval(refresh,10000);
