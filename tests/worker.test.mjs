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

test('balance reads the existing simulated ledger without placing orders',async()=>{
  const state={runner_version:1,ledger:{version:1,account:{
    cash:500,starting_equity:500,positions:{},trades:[]}},
    cursors:{BTCUSDT:1791553500000,ETHUSDT:1791553500000,SOLUSDT:1791553500000}};
  let hits=0;
  globalThis.fetch=async(url,opts)=>{
    hits++;
    assert.match(String(url),/\/contents\/runner\.json\?ref=paper-state$/);
    assert.equal(opts?.method,undefined);
    return new Response(JSON.stringify({encoding:'base64',content:btoa(JSON.stringify(state))}),
      {status:200,headers:{'content-type':'application/json'}});
  };
  try{
    const r=await worker.fetch(request(update('/balance')),env);
    assert.equal(r.status,200);
    const m=await r.json();
    assert.equal(hits,1);
    assert.match(m.text,/\$500\.00/);
    assert.match(m.text,/PAPER BALANCE/);
  }finally{globalThis.fetch=oldFetch}
});
