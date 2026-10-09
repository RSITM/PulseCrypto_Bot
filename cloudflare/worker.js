/**
 * PulseCrypto instant Telegram command webhook — READ-ONLY PAPER TRADING.
 * Configure TELEGRAM_WEBHOOK_SECRET and TELEGRAM_CHAT_ID as Cloudflare secrets.
 * No bot token, order placement, broker keys or changes to the Python strategy.
 */
const ROOT="https://api.github.com/repos/RSITM/PulseCrypto_Bot";
const SYMBOLS=["BTCUSDT","ETHUSDT","SOLUSDT"];
const FIFTEEN=900000;
const response=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});

async function github(path){
  const r=await fetch(ROOT+path,{headers:{"accept":"application/vnd.github+json","user-agent":"PulseCrypto-Paper-Telegram"}});
  if(!r.ok)throw Error("Could not read GitHub data");
  return r.json();
}
async function file(name){
  if(!["runner.json","signal_diagnostics.json"].includes(name))throw Error("Unsupported data");
  const data=await github("/contents/"+name+"?ref=paper-state");
  if(data.encoding!=="base64" || typeof data.content!=="string")throw Error("Invalid saved file");
  return JSON.parse(atob(data.content.replace(/\s/g,"")));
}
const usd=x=>"$"+Number(x).toFixed(2);
function account(data){
  if(data.runner_version!==1 || data.ledger?.version!==1)throw Error("Unexpected paper ledger version");
  const a=data.ledger.account;
  if(!a || !Array.isArray(a.trades) || !a.positions ||
     !Number.isFinite(a.cash) || !Number.isFinite(a.starting_equity) || a.starting_equity<=0)
     throw Error("Invalid paper balance");
  return a;
}
function lastCandle(state){
  const values=Object.values(state.cursors||{}).filter(Number.isSafeInteger);
  return values.length ? new Date(Math.max(...values)+FIFTEEN).toISOString().slice(0,16).replace("T"," ")+" UTC" : "Unavailable";
}
function balance(state){
  const a=account(state), positions=Object.entries(a.positions);
  const lines=["💰 PulseCrypto — PAPER BALANCE","Starting capital: "+usd(a.starting_equity),
    "Available simulated cash: "+usd(a.cash),"Open positions: "+positions.length,
    "Last processed candle: "+lastCandle(state)];
  if(!positions.length)lines.push("Account equity: "+usd(a.cash)+" (no open positions)");
  else {
    lines.push("Total equity unavailable without current market prices");
    for(const [sym,pos] of positions)lines.push("• "+sym.replace("USDT","")+" entry: "+usd(pos.entry));
  }
  return lines.join("\n");
}
function performance(state){
  const a=account(state), trades=a.trades, wins=trades.filter(t=>t.net_pnl>0).length,
    losses=trades.filter(t=>t.net_pnl<0).length;
  let running=a.starting_equity, peak=running, drawdown=0, pnl=0;
  for(const trade of trades){
    const p=Number(trade.net_pnl);
    if(!Number.isFinite(p))throw Error("Invalid trade P/L");
    pnl+=p;running+=p;peak=Math.max(peak,running);
    if(peak>0)drawdown=Math.max(drawdown,(peak-running)/peak*100);
  }
  return ["📊 PulseCrypto — PAPER PERFORMANCE",
    "Closed trades: "+trades.length+" | Wins: "+wins+" | Losses: "+losses,
    "Win rate: "+(trades.length?(100*wins/trades.length).toFixed(1)+"%":"N/A (no closed trades)"),
    "Realized net P/L: "+usd(pnl),"Closed-trade drawdown: "+drawdown.toFixed(2)+"%",
    "Available simulated cash: "+usd(a.cash),"Open positions: "+Object.keys(a.positions).length,
    "Last processed candle: "+lastCandle(state),
    "Simulated trades only; drawdown excludes open-position changes."].join("\n");
}
function trades(state){
  const records=account(state).trades;
  if(!records.length)return "🧾 PulseCrypto — PAPER TRADES\nNo completed trades yet.";
  return ["🧾 PulseCrypto — LAST 5 CLOSED PAPER TRADES",
    ...records.slice(-5).reverse().map(t=>"• "+String(t.symbol).replace("USDT","")+": "+usd(t.net_pnl)+" ("+String(t.reason).slice(0,35)+")")].join("\n");
}
function signals(data){
  if(data.version!==1 || !data.counts)throw Error("Invalid signal history");
  const count=new Map(),lines=["📡 PulseCrypto — PAPER SIGNALS"];
  for(const sym of SYMBOLS){
    const group=data.counts[sym];
    if(!group || typeof group!=="object")throw Error("Missing market history");
    let total=0;
    for(const [reason,n] of Object.entries(group)){
      if(typeof reason!=="string" || !Number.isSafeInteger(n) || n<0)throw Error("Invalid signal count");
      total+=n;count.set(reason,(count.get(reason)||0)+n);
    }
    lines.push(sym.replace("USDT","")+": "+total+" decisions");
  }
  if(count.size){
    lines.push("Most common decisions:");
    for(const [reason,n] of [...count].sort((a,b)=>b[1]-a[1]).slice(0,5))lines.push("• "+reason.slice(0,110)+": "+n);
  }else lines.push("No recorded decisions yet.");
  lines.push("History begins when diagnostics were enabled.");
  return lines.join("\n");
}
async function workflowStatus(name,limitMinutes){
  const result=await github("/actions/workflows/"+name+"/runs?branch=main&per_page=20");
  const finished=(result.workflow_runs||[]).filter(r=>r.status==="completed");
  const recent=finished[0];
  if(recent && recent.conclusion==="failure")return "NEEDS ATTENTION — latest run failed";
  const successful=finished.find(r=>r.conclusion==="success");
  if(!successful)return "NEEDS ATTENTION — no successful runs";
  const timestamp=Date.parse(successful.run_started_at || successful.created_at);
  if(!Number.isFinite(timestamp) || Date.now()-timestamp>limitMinutes*60000)return "NEEDS ATTENTION — last success too old";
  return "OK";
}
async function status(){
  const r=await Promise.allSettled([
    workflowStatus("paper-forward.yml",40), workflowStatus("turso-backup-test.yml",45), file("runner.json")
  ]);
  const scanner=r[0].status==="fulfilled"?r[0].value:"UNKNOWN — GitHub data unavailable",
    backup=r[1].status==="fulfilled"?r[1].value:"UNKNOWN — GitHub data unavailable";
  let candle="UNKNOWN — saved candle history unavailable",when="Unavailable";
  if(r[2].status==="fulfilled"){
    const data=r[2].value;when=lastCandle(data);
    const ok=SYMBOLS.every(sym=>{
      const opened=data.cursors?.[sym],closed=opened+FIFTEEN,age=Date.now()-closed;
      return Number.isSafeInteger(opened) && age>=-60000 && age<=45*60000;
    });
    candle=ok?"OK":"NEEDS ATTENTION — missing/stale candles";
  }
  return ["🩺 PulseCrypto — PAPER STATUS","Paper scanner: "+scanner,"Turso backup: "+backup,
    "Candle feed: "+candle,"Last processed candle: "+when,
    "Verified against GitHub workflow results and saved candle timestamps."].join("\n");
}
function help(){
  return ["🤖 PulseCrypto — PAPER COMMAND CENTER",
    "/status — scan, backup and market health",
    "/balance — simulated account balance",
    "/performance — paper results and drawdown",
    "/signals — signal rejection reasons",
    "/trades — last five paper trades",
    "/help — available commands",
    "Read-only: no real orders or strategy changes."].join("\n");
}
async function command(name){
  if(name==="/help"||name==="/start")return help();
  if(name==="/status")return status();
  if(name==="/signals"){
    try{return signals(await file("signal_diagnostics.json"))}
    catch{return "📡 PulseCrypto signal diagnostics aren't available yet."}
  }
  if(["/balance","/performance","/trades"].includes(name)){
    const data=await file("runner.json");
    return name==="/balance"?balance(data):name==="/performance"?performance(data):trades(data);
  }
  return "Unknown command. Send /help for available read-only commands.";
}
export default {
  async fetch(req,env){
    const url=new URL(req.url);
    if(url.pathname==="/"&&req.method==="GET")
      return new Response("PulseCrypto Telegram webhook ready — PAPER ONLY",{status:200});
    if(url.pathname!=="/telegram"||req.method!=="POST")return new Response("Not found",{status:404});
    if(!env.TELEGRAM_WEBHOOK_SECRET||!env.TELEGRAM_CHAT_ID)return new Response("Not configured",{status:503});
    if(req.headers.get("x-telegram-bot-api-secret-token")!==env.TELEGRAM_WEBHOOK_SECRET)
      return new Response("Unauthorized",{status:401});
    if(Number(req.headers.get("content-length")||0)>16000)return new Response("Too large",{status:413});
    let update;
    try{update=await req.json()}catch{return new Response("Invalid JSON",{status:400})}
    const message=update?.message,chat=message?.chat;
    if(!message||chat?.type!=="private"||String(chat.id)!==String(env.TELEGRAM_CHAT_ID))
      return new Response("OK",{status:200});
    const cmd=typeof message.text==="string"?message.text.trim().split(/\s+/)[0].toLowerCase():"";
    if(!cmd.startsWith("/")||cmd.includes("@"))return new Response("OK",{status:200});
    let text;
    try{text=await command(cmd)}catch{text="⚠️ PulseCrypto could not retrieve the latest data; try again shortly."}
    // Telegram can send a bot message directly from the webhook HTTP response.
    // The Worker never stores a Telegram bot token.
    return response({method:"sendMessage",chat_id:chat.id,text:text.slice(0,4000),disable_web_page_preview:true});
  }
};
