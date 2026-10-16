/* 精确版本的同源静态资源缓存；IndexedDB 和用户文件不归服务工作线程管理。 */
const VERSION='reactmono-__CACHE_VERSION__';
const PRECACHE=['./','./index.html','./style.css','./ui/app.js','./core/game.js',
 './core/agent.js','./storage/indexeddb.js','./core/save.js',
 './vendor/react.production.min.js','./vendor/react-dom.production.min.js',
 './manifest.webmanifest','./icons/icon-192.png','./icons/icon-512.png'];
const urls=PRECACHE.map(path=>new URL(path,self.registration.scope).href);
const origin=new URL(self.registration.scope).origin;
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(VERSION).then(cache=>cache.addAll(urls)));
  // 不自动 skipWaiting：旧对局仍用一致的旧脚本，玩家确认后才切换。
});
self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{
    const names=await caches.keys();
    await Promise.all(names.filter(name=>name.startsWith('reactmono-')&&name!==VERSION).map(name=>caches.delete(name)));
    await self.clients.claim();
  })());
});
self.addEventListener('message',event=>{
  if(event.data==='SKIP_WAITING') self.skipWaiting();
});
self.addEventListener('fetch',event=>{
  const request=event.request,url=new URL(request.url);
  if(request.method!=='GET'||url.origin!==origin||!url.href.startsWith(self.registration.scope))return;
  if(request.mode==='navigate'){
    // 始终先返回与缓存脚本同版本的页面；版本切换由玩家确认。
    event.respondWith(caches.match(new URL('./index.html',self.registration.scope).href)
      .then(hit=>hit||fetch(request).catch(()=>Response.error())));
    return;
  }
  if(urls.includes(url.href)){
    event.respondWith(caches.match(request).then(hit=>hit||fetch(request)));
  }
});
