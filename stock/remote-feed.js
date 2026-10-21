(function(){
'use strict';
var MANIFEST='https://raw.githubusercontent.com/healingmart/image/main/stock/manifest.json';
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function params(){
 var p=new URLSearchParams(location.search), cat=(p.get('cat')||'').trim();
 var m=location.pathname.match(/^\/search\/label\/([^/?#]+)/);
 if(m&&!cat){try{cat=decodeURIComponent(m[1].replace(/\+/g,' '))}catch(e){}}
 return {q:(p.get('q')||'').trim(),cat:cat,filters:['배경','방향','해상도','재생'].map(function(k){return (p.get(k)||'').trim()}).filter(Boolean)}
}
function tagsOf(x){return Array.isArray(x.tags)?x.tags:[]}
function card(x){
 var tags=tagsOf(x).filter(function(t){return t&&t!=='HM-스톡'&&t!=='이미지'}).slice(0,3);
 var tagHtml=tags.map(function(t){return '<span class="hmstock-card-tag">'+esc(t)+'</span>'}).join('');
 var badge=x.transparent?'PNG 투명':'FREE';
 var img=x.thumb_url||x.url||'';
 var url=x.download_url||x.url||'#';
 return '<article class="hmstock-card hmstock-remote-card" data-hmstock-id="'+esc(x.id||'')+'">'+
 '<a class="hmstock-card-thumb" href="'+esc(url)+'" target="_blank" rel="noopener">'+
 '<img alt="'+esc(x.title||'HealingMart Stock')+'" loading="lazy" decoding="async" src="'+esc(img)+'"/>'+
 '<span class="hmstock-card-badge">'+badge+'</span>'+
 '<span class="hmstock-card-play"><i class="bi bi-download"></i></span></a>'+
 '<div class="hmstock-card-body">'+
 '<a class="hmstock-card-title" href="'+esc(url)+'" target="_blank" rel="noopener">'+esc(x.title||'제목 없는 스톡')+'</a>'+
 '<div class="hmstock-card-meta">'+tagHtml+'</div></div></article>'
}
function match(x,state){
 var tags=tagsOf(x), cats=Array.isArray(x.categories)?x.categories:[x.category].filter(Boolean);
 var wanted=[state.cat].concat(state.filters).filter(Boolean);
 if(wanted.some(function(v){return tags.indexOf(v)<0&&cats.indexOf(v)<0}))return false;
 if(state.q){
   var hay=((x.title||'')+' '+tags.join(' ')+' '+cats.join(' ')).toLowerCase();
   if(hay.indexOf(state.q.toLowerCase())<0)return false;
 }
 return true
}
function render(data){
 var grid=document.getElementById('hmstock-grid'); if(!grid)return;
 var state=params(), all=Array.isArray(data.items)?data.items:[], items=all.filter(function(x){return x&&x.kind==='image'&&match(x,state)});
 grid.innerHTML=items.map(card).join('');
 var count=document.getElementById('hmstock-count'); if(count)count.textContent=items.length+'개 이미지 스톡';
 var status=document.getElementById('hmstock-browser-status'); if(status)status.textContent='HealingMart 자동 스톡 · 최신순';
 var title=document.getElementById('hmstock-browser-title');
 if(title){
   if(state.q)title.textContent='“'+state.q+'” 검색 결과';
   else if(state.cat)title.textContent=state.cat+' 스톡';
   else title.textContent='전체 이미지 스톡';
 }
 var more=document.getElementById('hmstock-more'); if(more)more.style.display='none';
 var empty=document.getElementById('hmstock-empty');
 if(empty){
   empty.style.display=items.length?'none':'flex';
   if(!items.length){
     var b=empty.querySelector('b'),s=empty.querySelector('span');
     if(b)b.textContent='조건에 맞는 이미지 스톡이 없습니다.';
     if(s)s.textContent='다른 검색어나 카테고리를 선택해 보세요.';
   }
 }
 document.documentElement.setAttribute('data-hmstock-remote','ready');
 window.dispatchEvent(new CustomEvent('hmstock:manifest',{detail:{count:items.length,total:all.length}}));
}
function load(){
 fetch(MANIFEST+'?v='+Date.now(),{cache:'no-store'})
  .then(function(r){if(!r.ok)throw new Error('manifest '+r.status);return r.json()})
  .then(render)
  .catch(function(e){console.warn('[HealingMart Stock] remote manifest unavailable',e)});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(load,80)});
else setTimeout(load,80);
})();