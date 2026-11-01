/* Offline browser regression. Run with Electron; no social requests are made. */
"use strict";
const {app, BrowserWindow} = require("electron");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "../autopilot/static");
const writes = [];
const state = {
  settings: {enabled:false, per_day:5, max_pending:5, gap_hours:1, day_start:"09:00", timezone:"America/New_York", twitch_client_id:"", instagram_id:"12", instagram_username:"fixturebrand", accounts:[{id:"12",platform:"instagram",username:"fixturebrand"}]},
  connections:{twitch:true,twitch_login:"fixtureviewer",woopsocial:true},
  watches:[{id:1,login:"fixturechannel",min_views:10000,enabled:true,mode:"ask",options:{captions:true},last_polled:0,error:""}],
  clips:[{id:"fixture",title:"Fixture viewer clip <script>not executable</script>",views:12000,creator:"fixtureviewer",state:"review",reached_at:0,duration:60,source_url:"https://clips.twitch.tv/fixture",media_url:"",options:{captions:true}}],
  counts:{pending:1,review:1,scheduled:0,published:0},posts:[],events:[]
};
app.disableHardwareAcceleration();
app.whenReady().then(async () => {
  const server = http.createServer((req,res) => {
    if(req.url.startsWith("/api/")) {
      if(req.method !== "GET") { writes.push(req.url); if(req.url.endsWith("/approve")) state.clips[0].state="scheduled"; }
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
    assert.ok(await js(`document.body.innerText.includes('Schedule to @fixturebrand')`),"Exact destination visible before approval");
    assert.equal(await js(`document.querySelectorAll('.clip-body script').length`),0,"Titles must be text");
    await js(`document.getElementById('damage-open').click()`);await pause();
    assert.ok(await js(`document.getElementById('damage-dialog').open`));
    assert.equal(writes.length,0,"Satire must not make requests");
    await js(`document.getElementById('damage-dialog').close();document.querySelector('.clip-body .primary').click()`);await pause();
    assert.deepEqual(writes,["/api/clips/fixture/approve"],"One approval goes directly to schedule");
    await js(`document.getElementById('settings-open').click()`);await pause();
    assert.equal(await js(`document.querySelector('[name=per_day]').value`),"5");
    assert.equal(await js(`document.getElementById('instagram').selectedOptions[0].textContent`),"@fixturebrand");
    await js(`document.getElementById('settings-dialog').close()`);
    assert.ok(await js(`document.documentElement.scrollWidth <= window.innerWidth`),"Desktop should not overflow");
    win.setSize(390,844);await pause();
    assert.ok(await js(`document.documentElement.scrollWidth <= window.innerWidth`),"Mobile should not overflow");
    console.log(JSON.stringify({ok:true,noWritesOnMount:true,exactDestination:true,oneApproval:true,satireNoRequests:true,responsive:true}));
    server.close();win.destroy();app.exit(0);
  }catch(error){console.error(error.message);server.close();win.destroy();app.exit(1);}
}).catch(error=>{console.error(error.message);app.exit(1);});
