import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../cloudflare/worker.js';

const origin='https://pulsecrypto-telegram.example.workers.dev';
const env={TELEGRAM_WEBHOOK_SECRET:'test-secret-value',TELEGRAM_CHAT_ID:'12345'};
const oldFetch=globalThis.fetch;
const update=(text='/help',id=12345)=>({update_id:1000,message:{chat:{id,type:'private'},text}});
const request=(body,secret='test-secret-value')=>new Request(origin+'/telegram',{
  method:'POST',headers:{'x-telegram-bot-api-secret-token':secret},body:JSON.stringify(body)
});

test('health route is ready but does not expose configuration',async()=>{
  const r=await worker.fetch(new Request(origin+'/'),env);
  assert.equal(r.status,200);
  const t=await r.text();
  assert.match(t,/PAPER ONLY/);
  assert.doesNotMatch(t,/test-secret-value/);
});

test('unauthenticated Telegram request is rejected',async()=>{
  globalThis.fetch=()=>{throw Error('Must not fetch GitHub')};
  try{
    const r=await worker.fetch(request(update(), 'invalid'),env);
    assert.equal(r.status,401);
  }finally{globalThis.fetch=oldFetch}
});

test('messages from unrelated private chats are ignored',async()=>{
  globalThis.fetch=()=>{throw Error('Must not fetch GitHub')};
  try{
    const r=await worker.fetch(request(update('/balance',999)),env);
    assert.equal(r.status,200);
    assert.equal(await r.text(),'OK');
  }finally{globalThis.fetch=oldFetch}
});

test('help command returns immediate read-only Telegram response',async()=>{
  globalThis.fetch=()=>{throw Error('Help must not fetch GitHub')};
  try{
    const r=await worker.fetch(request(update()),env);
    assert.equal(r.status,200);
    const m=await r.json();
    assert.equal(m.method,'sendMessage');
    assert.equal(m.chat_id,12345);
    assert.match(m.text,/\/status/);
    assert.match(m.text,/Read-only/);
  }finally{globalThis.fetch=oldFetch}
});

test('balance uses public raw paper ledger without submitting trades',async()=>{
  const state={runner_version:1,ledger:{version:1,account:{
    cash:500,starting_equity:500,positions:{},trades:[]}},
    cursors:{BTCUSDT:1791553500000,ETHUSDT:1791553500000,SOLUSDT:1791553500000}};
  const calls=[];
  globalThis.fetch=async(url,opts)=>{
    calls.push(String(url));
    assert.match(String(url),/raw.githubusercontent.com\/RSITM\/PulseCrypto_Bot\/paper-state\/runner\.json$/);
    assert.equal(opts?.method,undefined);
    return new Response(JSON.stringify(state),{status:200});
  };
  try{
    const r=await worker.fetch(request(update('/balance')),env);
    assert.equal(r.status,200);
    const m=await r.json();
    assert.equal(calls.length,1);
    assert.match(m.text,/\$500\.00/);
    assert.match(m.text,/PAPER BALANCE/);
  }finally{globalThis.fetch=oldFetch}
});

test('signals reads recorded public diagnostic counts even when GitHub REST API is rate limited',async()=>{
  const history={version:1,counts:{
    BTCUSDT:{"WAIT: 15m trend not bullish":35,"WAIT: Insufficient volatility":2},
    ETHUSDT:{"WAIT: 15m trend not bullish":37},
    SOLUSDT:{"WAIT: 15m trend not bullish":37}},recent:[]};
  const calls=[];
  globalThis.fetch=async(url)=>{
    calls.push(String(url));
    if(String(url).startsWith('https://api.github.com/')){
      return new Response('rate limited',{status:403});
    }
    assert.match(String(url),/raw.githubusercontent.com\/RSITM\/PulseCrypto_Bot\/paper-state\/signal_diagnostics\.json$/);
    return new Response(JSON.stringify(history),{status:200});
  };
  try{
    const r=await worker.fetch(request(update('/signals')),env);
    assert.equal(r.status,200);
    const m=await r.json();
    assert.match(m.text,/BTC: 37 decisions/);
    assert.match(m.text,/ETH: 37 decisions/);
    assert.match(m.text,/SOL: 37 decisions/);
    assert.match(m.text,/15m trend not bullish/);
    assert.equal(calls.length,1);
  }finally{globalThis.fetch=oldFetch}
});

test('REST contents API is a fallback when raw GitHub is temporarily unavailable',async()=>{
  const state={runner_version:1,ledger:{version:1,account:{
    cash:500,starting_equity:500,positions:{},trades:[]}},cursors:{}};
  const calls=[];
  globalThis.fetch=async(url)=>{
    calls.push(String(url));
    if(String(url).startsWith('https://raw.githubusercontent.com/'))
      return new Response('unavailable',{status:503});
    assert.match(String(url),/\/contents\/runner\.json\?ref=paper-state$/);
    return new Response(JSON.stringify({encoding:'base64',content:btoa(JSON.stringify(state))}),{status:200});
  };
  try{
    const r=await worker.fetch(request(update('/balance')),env);
    const m=await r.json();
    assert.match(m.text,/\$500\.00/);
    assert.equal(calls.length,2);
  }finally{globalThis.fetch=oldFetch}
});

test('status reports GitHub API 403 rather than suggesting a confirmed scanner outage',async()=>{
  const state={runner_version:1,ledger:{version:1,account:{
    cash:500,starting_equity:500,positions:{},trades:[]}},
    cursors:{BTCUSDT:1791553500000,ETHUSDT:1791553500000,SOLUSDT:1791553500000}};
  globalThis.fetch=async(url)=>{
    if(String(url).startsWith('https://raw.githubusercontent.com/'))
      return new Response(JSON.stringify(state),{status:200});
    return new Response('rate limited',{status:403});
  };
  try{
    const r=await worker.fetch(request(update('/status')),env);
    const m=await r.json();
    assert.match(m.text,/UNKNOWN — GitHub API HTTP 403/);
    assert.match(m.text,/Last processed candle/);
  }finally{globalThis.fetch=oldFetch}
});


test('missing active production secret bindings give 503 and only print binding names',async()=>{
  const originalLog=console.error;
  const recorded=[];
  console.error=(message)=>recorded.push(String(message));
  try{
    const r=await worker.fetch(request(update('/help')),{},);
    assert.equal(r.status,503);
    assert.match(await r.text(),/configuration incomplete/);
    assert.equal(recorded.length,1);
    assert.match(recorded[0],/TELEGRAM_CHAT_ID/);
    assert.match(recorded[0],/TELEGRAM_WEBHOOK_SECRET/);
    assert.doesNotMatch(recorded[0],/test-secret-value|12345/);
  }finally{
    console.error=originalLog;
  }
});


test('public readiness returns 503 when production secrets are not bound',async()=>{
  const result=await worker.fetch(new Request(origin+'/ready'),{});
  assert.equal(result.status,503);
  const body=await result.text();
  assert.match(body,/not configured/);
  assert.doesNotMatch(body,/TELEGRAM_CHAT_ID|TELEGRAM_WEBHOOK_SECRET|12345|test-secret-value/);
});

test('public readiness returns 200 only after both bindings are present',async()=>{
  const result=await worker.fetch(new Request(origin+'/ready'),env);
  assert.equal(result.status,200);
  assert.match(await result.text(),/configured/);
});

test('Cloudflare deploy config preserves dashboard variables and requires Telegram secrets',async()=>{
  const {readFileSync}=await import('node:fs');
  const config=readFileSync(new URL('../wrangler.toml',import.meta.url),'utf8');
  assert.match(config,/^keep_vars\s*=\s*true\s*$/m);
  assert.match(config,/^\[secrets\]\s*$/m);
  assert.match(config,/^required\s*=\s*\["TELEGRAM_CHAT_ID",\s*"TELEGRAM_WEBHOOK_SECRET"\]\s*$/m);
  assert.doesNotMatch(config,/TELEGRAM_CHAT_ID\s*=|TELEGRAM_WEBHOOK_SECRET\s*=/);
});
