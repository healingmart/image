(function(){
'use strict';
var MANIFEST='https://cdn.jsdelivr.net/gh/healingmart/image@main/stock/manifest.json';
var CATEGORIES='https://cdn.jsdelivr.net/gh/healingmart/image@main/stock/categories.json';
var cache=null,catCache=null,rendering=false,observer=null;

function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function state(){
  var p=new URLSearchParams(location.search),cat=(p.get('cat')||'').trim(),m=location.pathname.match(/^\/search\/label\/([^/?#]+)/);
  if(m&&!cat){try{cat=decodeURIComponent(m[1].replace(/\+/g,' '))}catch(e){}}
  return {q:(p.get('q')||'').trim(),cat:cat,filters:['배경','방향','해상도','재생'].map(function(k){return (p.get(k)||'').trim()}).filter(Boolean)}
}
function tags(x){return Array.isArray(x.tags)?x.tags:[]}
function categoriesOf(x){return Array.isArray(x.categories)?x.categories:[x.category].filter(Boolean)}
function categoryPath(x){return categoriesOf(x).join('/')}
function categoryActive(x){
  if(!catCache||!Array.isArray(catCache.paths))return true;
  var p=categoryPath(x);
  return !p||catCache.paths.indexOf(p)>=0;
}
function categoryHref(name){return '/?cat='+encodeURIComponent(name)}
function renderCategoryUi(data){
  if(!data||!Array.isArray(data.categories))return;
  var s=state(),tops=data.categories.map(function(x){return x&&x.name}).filter(Boolean);

  var nav=document.querySelector('.hmstock-nav');
  if(nav){
    var navNames=tops.slice(0,6);
    nav.innerHTML='<a href="/?cat=" class="'+(!s.cat?'is-active':'')+'">전체</a>'+
      navNames.map(function(n){return '<a href="'+categoryHref(n)+'" class="'+(s.cat===n?'is-active':'')+'">'+esc(n)+'</a>'}).join('');
  }

  var chips=document.querySelector('.hmstock-chips');
  if(chips){
    chips.innerHTML='<a href="/?cat=" class="'+(!s.cat?'is-active':'')+'">전체</a>'+
      tops.map(function(n){return '<a href="'+categoryHref(n)+'" class="'+(s.cat===n?'is-active':'')+'">'+esc(n)+'</a>'}).join('');
  }
  document.documentElement.setAttribute('data-hmstock-categories','ready');
}
function card(x){
  var ts=tags(x).filter(function(t){return t&&t!=='HM-스톡'&&t!=='이미지'}).slice(0,3);
  var th=ts.map(function(t){return '<span class="hmstock-card-tag">'+esc(t)+'</span>'}).join('');
  var badge=x.transparent?'투명 WEBP':'FREE',img=x.thumb_url||x.preview_url||x.url||'',url=x.download_url||x.url||'#';
  return '<article class="hmstock-card hmstock-remote-card" data-hmstock-id="'+esc(x.id||'')+'">'+
    '<a class="hmstock-card-thumb" href="'+esc(url)+'" target="_blank" rel="noopener">'+
    '<img alt="'+esc(x.title||'HealingMart Stock')+'" loading="lazy" decoding="async" src="'+esc(img)+'"/>'+
    '<span class="hmstock-card-badge">'+badge+'</span><span class="hmstock-card-play"><i class="bi bi-download"></i></span></a>'+
    '<div class="hmstock-card-body"><a class="hmstock-card-title" href="'+esc(url)+'" target="_blank" rel="noopener">'+esc(x.title||'제목 없는 스톡')+'</a>'+
    '<div class="hmstock-card-meta">'+th+'</div></div></article>'
}
function match(x,s){
  var ts=tags(x),cs=categoriesOf(x),w=[s.cat].concat(s.filters).filter(Boolean);
  if(w.some(function(v){return ts.indexOf(v)<0&&cs.indexOf(v)<0}))return false;
  if(s.q){
    var h=((x.title||'')+' '+ts.join(' ')+' '+cs.join(' ')).toLowerCase();
    if(h.indexOf(s.q.toLowerCase())<0)return false
  }
  return true
}
function render(data){
  var grid=document.getElementById('hmstock-grid');if(!grid||!data)return;
  rendering=true;
  var s=state(),all=Array.isArray(data.items)?data.items:[],
      items=all.filter(function(x){return x&&x.kind==='image'&&categoryActive(x)&&match(x,s)});
  grid.innerHTML=items.map(card).join('');
  var count=document.getElementById('hmstock-count');if(count)count.textContent=items.length+'개 이미지 스톡';
  var status=document.getElementById('hmstock-browser-status');if(status)status.textContent='HealingMart 자동 스톡 · 최신순';
  var title=document.getElementById('hmstock-browser-title');if(title){if(s.q)title.textContent='“'+s.q+'” 검색 결과';else if(s.cat)title.textContent=s.cat+' 스톡';else title.textContent='전체 이미지 스톡'}
  var more=document.getElementById('hmstock-more');if(more)more.style.display='none';
  var empty=document.getElementById('hmstock-empty');
  if(empty){empty.style.display=items.length?'none':'flex';if(!items.length){var b=empty.querySelector('b'),sp=empty.querySelector('span');if(b)b.textContent='조건에 맞는 이미지 스톡이 없습니다.';if(sp)sp.textContent='다른 검색어나 카테고리를 선택해 보세요.'}}
  document.documentElement.setAttribute('data-hmstock-remote','ready');
  setTimeout(function(){rendering=false},0);
}
function defend(){
  var grid=document.getElementById('hmstock-grid');if(!grid||observer)return;
  observer=new MutationObserver(function(){
    if(rendering||!cache)return;
    clearTimeout(defend.t);
    defend.t=setTimeout(function(){if(!document.querySelector('.hmstock-remote-card'))render(cache)},80)
  });
  observer.observe(grid,{childList:true,subtree:false});
}
function fetchJson(url){
  return fetch(url+'?v='+Date.now(),{cache:'no-store'}).then(function(r){if(!r.ok)throw new Error(url+' '+r.status);return r.json()})
}
function boot(){
  defend();
  Promise.all([
    fetchJson(MANIFEST),
    fetchJson(CATEGORIES).catch(function(e){console.warn('[HealingMart Stock] categories unavailable',e);return null})
  ]).then(function(res){
    cache=res[0];catCache=res[1];
    renderCategoryUi(catCache);
    render(cache);
    [300,1000,2500,5000].forEach(function(ms){setTimeout(function(){renderCategoryUi(catCache);render(cache)},ms)})
  }).catch(function(e){console.warn('[HealingMart Stock] remote manifest unavailable',e)});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(boot,50)});else setTimeout(boot,50);
})();