/* Offline browser regression. Run with Electron; no social requests are made. */
"use strict";
const {app, BrowserWindow} = require("electron");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "../autopilot/static");
const writes = [];
const requests = [];
const bodies = [];
const state = {
  settings: {enabled:false, per_day:5, max_pending:5, gap_hours:1, day_start:"09:00", timezone:"America/New_York", twitch_client_id:"", instagram_id:"12", instagram_username:"fixturebrand", destination_revision:"a".repeat(64), selected_destinations:[{id:"12",platform:"instagram",username:"fixturebrand"}], accounts:[{id:"12",platform:"instagram",username:"fixturebrand"},{id:"56",platform:"tiktok",username:"fixturevideo"},{id:"78",platform:"youtube",username:"fixturechannel"}]},
  connections:{twitch:true,twitch_login:"fixtureviewer",woopsocial:true},
  watches:[{id:1,login:"fixturechannel",min_views:10000,enabled:true,mode:"ask",options:{captions:true},last_polled:0,error:""}],
  clips:[{id:"fixture",title:"Fixture viewer clip <script>not executable</script>",views:12000,creator:"fixtureviewer",state:"review",reached_at:0,duration:60,source_url:"https://clips.twitch.tv/fixture",media_url:"",options:{captions:true}}],
  counts:{pending:1,review:1,scheduled:0,published:0},posts:[],events:[]
};
app.disableHardwareAcceleration();
app.whenReady().then(async () => {
  const server = http.createServer(async (req,res) => {
    requests.push(req.url);
    if(req.url.startsWith("/api/")) {
      if(req.method !== "GET") {
        const chunks=[];for await(const chunk of req)chunks.push(chunk);const body=JSON.parse(Buffer.concat(chunks).toString() || "{}");bodies.push({path:req.url,body});
        writes.push(req.url); if(req.url.endsWith("/approve")) state.clips[0].state="scheduled";
        if(req.url==="/api/destinations") {state.settings.selected_destinations=body.account_ids.map(id=>state.settings.accounts.find(a=>a.id===id));state.settings.destination_revision="b".repeat(64);}
      }
      res.setHeader("Content-Type","application/json");res.end(JSON.stringify(req.url==="/api/status" ? state : {saved:true}));return;
    }
    const file = req.url === "/" ? "index.html" : req.url === "/static/app.js" ? "app.js" : req.url === "/static/app.css" ? "app.css" : null;
    if(!file) {res.writeHead(404);res.end();return;}
    res.setHeader("Content-Type",file.endsWith("js") ? "text/javascript" : file.endsWith("css") ? "text/css" : "text/html");res.end(fs.readFileSync(path.join(root,file)));
  });
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  const win = new BrowserWindow({show:false,width:1440,height:1100,webPreferences:{sandbox:true,contextIsolation:true,offscreen:true}});
  const js = code=>win.webContents.executeJavaScript(code);
  const pause=()=>new Promise(resolve=>setTimeout(resolve,180));
  try {
    await win.loadURL(`http://127.0.0.1:${server.address().port}/`);await pause();
    assert.equal(writes.length,0,"Rendering the dashboard must not mutate state");
    assert.deepEqual(await js(`Array.from(document.querySelectorAll('.clip-body .buttons button')).map(b=>b.textContent)`),
      ["Schedule to @fixturebrand", "Damage Control", "Deny"], "Ready clips expose Schedule, Damage Control and Deny in order");
    const beforeDamageControl = requests.length;
    await js(`document.querySelectorAll('.clip-body .buttons button')[1].click()`);await pause();
    assert.ok(await js(`document.getElementById('damage-dialog').open`), "The clip action opens Damage Control");
    assert.equal(writes.length,0,"Damage Control must not schedule or delete anything");
    assert.equal(requests.length,beforeDamageControl,"Opening clip Damage Control makes no request");
    assert.ok(!await js(`document.getElementById('damage-dialog').textContent.toLowerCase().includes('joke button')`));
    await js(`document.getElementById('damage-dialog').close()`);
    assert.ok(await js(`document.body.innerText.includes('Schedule to @fixturebrand')`),"Exact destination visible before approval");
    assert.equal(await js(`document.querySelectorAll('.clip-body script').length`),0,"Titles must be text");
    await js(`document.getElementById('damage-open').click()`);await pause();
    assert.ok(await js(`document.getElementById('damage-dialog').open`));
    assert.equal(writes.length,0,"Satire must not make requests");
    await js(`document.getElementById('damage-dialog').close();document.querySelector('.clip-body .primary').click()`);await pause();
    assert.deepEqual(writes,["/api/clips/fixture/approve"],"One approval goes directly to schedule");
    await js(`document.getElementById('settings-open').click()`);await pause();
    assert.equal(await js(`document.querySelector('[name=per_day]').value`),"5");
    assert.equal(await js(`document.querySelector('[data-account-id="12"]').checked`),true);
    assert.equal(await js(`document.querySelector('[data-account-id="56"]').checked`),false,"Connected TikTok stays unselected");
    assert.equal(await js(`document.querySelector('[data-account-id="78"]').checked`),false,"Connected YouTube stays unselected");
    state.clips[0].state="review";
    await js(`document.querySelector('[data-account-id="56"]').click();document.getElementById('settings-form').requestSubmit()`);await pause();
    assert.equal(await js(`document.querySelector('.clip-body .primary').textContent`),"Schedule to 2 profiles");
    assert.ok(await js(`document.querySelector('.clip-body').textContent.includes('TikTok @fixturevideo')`));
    writes.length=0;
    await js(`document.querySelector('.clip-body .primary').click()`);await pause();
    assert.deepEqual(writes,["/api/clips/fixture/approve"],"Multiple profiles still need just one schedule approval");
    assert.deepEqual(bodies.at(-1).body.account_ids,["12","56"]);
    assert.equal(bodies.at(-1).body.destination_revision,"b".repeat(64));
    assert.ok(await js(`document.documentElement.scrollWidth <= window.innerWidth`),"Desktop should not overflow");
    win.setSize(390,844);await pause();
    assert.ok(await js(`document.documentElement.scrollWidth <= window.innerWidth`),"Mobile should not overflow");
    console.log(JSON.stringify({ok:true,noWritesOnMount:true,exactDestination:true,explicitProfiles:true,noImplicitTiktokOrYoutube:true,oneApproval:true,satireNoRequests:true,responsive:true}));
    server.close();win.destroy();app.exit(0);
  }catch(error){console.error(error.message);server.close();win.destroy();app.exit(1);}
}).catch(error=>{console.error(error.message);app.exit(1);});
