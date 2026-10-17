"""P4 #72 real Chromium release profiling + visual + offline/autosave stress.
Compares candidate local dist against the already-published previous dev using the SAME browser runner.
All timings are noisy CI wall-clock observations, never a physical-phone claim.
"""
import hashlib,json,re,time,statistics,os
from pathlib import Path
from threading import Thread
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
OUT=Path('artifacts/issue72')
PUBLIC='https://siliconyc.github.io/ReactMono/'
SCENARIOS=[
 ('desktop-classic-2',1440,900,'classic-24',2),
 ('desktop-harbor-4',1280,800,'harbor-20',4),
 ('phone-classic-4',390,844,'classic-24',4),
 ('small-phone-harbor-3',320,640,'harbor-20',3)
]
SCRIPTS="""{
  window.__releaseLongTasks=[];
  try{new PerformanceObserver(list=>{
    for(const e of list.getEntries())window.__releaseLongTasks.push(Math.round(e.duration))
  }).observe({type:'longtask',buffered:true})}catch{}
  window.__releasePuts=0;
  const p=IDBObjectStore.prototype.put;
  IDBObjectStore.prototype.put=function(...args){
    if(this.name==='slots')window.__releasePuts++;
    return p.apply(this,args);
  };
  window.__releaseOscStart=0;window.__releaseOscEnd=0;
  if(window.OscillatorNode){
    const start=OscillatorNode.prototype.start;
    OscillatorNode.prototype.start=function(...args){
      window.__releaseOscStart++;
      this.addEventListener('ended',()=>window.__releaseOscEnd++,{once:true});
      return start.apply(this,args);
    };
  }
}"""
def identity(page):
 return page.evaluate("""()=>{
   const a=s=>{const r=document.querySelector(s)?.getBoundingClientRect();return r?
     {x:Math.round(r.x+scrollX),y:Math.round(r.y+scrollY),w:Math.round(r.width),h:Math.round(r.height)}:null;};
   const tiles=[...document.querySelectorAll('.tile')];
   const imgs=[...document.querySelectorAll('.character-image')];
   const buttons=[...document.querySelectorAll('.turn-card button')].filter(e=>{
     const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&!e.disabled;});
   return {tiles:tiles.length,board:a('.board'),currentAction:a('.turn-card'),firstPrimary:a('.turn-card .primary-btn'),
      docW:document.documentElement.scrollWidth,viewportW:innerWidth,markers:imgs.length,
      imagesLoaded:imgs.every(x=>x.complete&&x.naturalWidth>0),
      under44Active:buttons.filter(x=>x.getBoundingClientRect().height<44).map(x=>x.textContent.trim().slice(0,30)),
      gameplayStatus:document.querySelector('main')?.dataset.gameStatus};
 }""")
def metrics(page):
 return page.evaluate("""()=>{
   const n=performance.getEntriesByType('navigation')[0];
   const fcp=performance.getEntriesByType('paint').find(x=>x.name==='first-contentful-paint');
   const mem=performance.memory?.usedJSHeapSize??null;
   const entries=performance.getEntriesByType('resource');
   const sorted=[...(window.__releaseLongTasks??[])].sort((a,b)=>a-b);
   return {domContentLoadedMs:Math.round(n?.domContentLoadedEventEnd??0),
     pageLoadMs:Math.round(n?.loadEventEnd??0),fcpMs:fcp?Math.round(fcp.startTime):null,
     resources:entries.length,decodedResourceBytes:entries.reduce((a,x)=>a+(x.decodedBodySize||0),0),
     transferBytes:entries.reduce((a,x)=>a+(x.transferSize||0),0),
     longTasks:sorted.length,largestLongTaskMs:sorted.at(-1)??0,
     longTaskTotalMs:sorted.reduce((a,b)=>a+b,0),usedJsHeapBytes:mem,
     indexedDbPuts:window.__releasePuts??0,oscillatorStarts:window.__releaseOscStart??0,
     oscillatorEnds:window.__releaseOscEnd??0};
 }""")
def screenshot(page,name):
 path=OUT/(name+'.png')
 page.screenshot(path=str(path),full_page=True,animations='disabled')
 return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def sample_frames(page):
 result=page.evaluate("""async()=>{
   const gaps=[];let last=0;
   await new Promise(resolve=>{
     const sample=t=>{
       if(last)gaps.push(t-last);
       last=t;
       if(gaps.length>=75)return resolve();
       requestAnimationFrame(sample);
     };requestAnimationFrame(sample);
   });
   const s=gaps.sort((a,b)=>a-b);
   return {samples:s.length,medianMs:Math.round(s[Math.floor(s.length/2)]*10)/10,
     p95Ms:Math.round(s[Math.floor(s.length*.95)]*10)/10,
     over50Ms:s.filter(x=>x>50).length};
 }""")
 return result
def configure(page,board,seats,seed='7217'):
 page.get_by_label('游戏地图').select_option(board)
 page.get_by_label('玩家人数').select_option(str(seats))
 page.get_by_label('对局种子').fill(seed)
 page.get_by_label('最多轮数').fill('8')
 page.get_by_label('启用医院、监狱与商店').check()
 page.get_by_label('快速模式').check()
 for i in range(seats):
  page.get_by_label(f'第 {i+1} 位玩家类型').select_option('computer')
  page.get_by_label(f'第 {i+1} 位电脑策略').select_option(['conservative','balanced','aggressive'][i%3])
def auto_revision(page):
 return page.evaluate("""async()=>{
   return await new Promise((resolve,reject)=>{
      const request=indexedDB.open('reactmono-local-saves',1);
      request.onerror=()=>reject(request.error?.message);
      request.onsuccess=()=>{
        const db=request.result,tx=db.transaction('slots','readonly');
        const get=tx.objectStore('slots').get('auto');
        get.onsuccess=()=>{const row=get.result;resolve(row?JSON.parse(row.contents).game.revision:null);db.close()};
        get.onerror=()=>{reject(get.error?.message);db.close()};
      };
   })
 }""")
def scenario(browser,url,label,width,height,board,seats,offline=False):
 ctx=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,
   service_workers='allow',is_mobile=width<=390,has_touch=width<=390,reduced_motion='reduce')
 page=ctx.new_page();errors=[]
 page.on('pageerror',lambda err:errors.append(str(err)))
 page.on('dialog',lambda dialog:dialog.accept())
 page.add_init_script(SCRIPTS)
 response=page.goto(url,wait_until='load',timeout=30000)
 assert response and response.status==200,(label,response.status if response else None)
 page.wait_for_function("document.querySelector('.board')!==null")
 setup=identity(page);start_metrics=metrics(page)
 assert setup['docW']<=width+2,(label,setup)
 configure(page,board,seats)
 audioStress=label=='candidate-desktop-classic-2'
 if audioStress:
  # Opt-in after a genuine user gesture; verify oscillators finish/disconnect
  # even during many successive AI actions.
  page.get_by_role('button',name='开启音效').click()
 # Include the full CPU game in wall time, not just the polling after 75 rAF frames.
 start=time.monotonic()
 page.get_by_role('button',name=re.compile('开始游戏')).click()
 page.wait_for_function("document.querySelectorAll('.character-image').length>0 && [...document.querySelectorAll('.character-image')].every(e=>e.complete&&e.naturalWidth>0)",timeout=12000)
 initial=identity(page)
 assert initial['tiles']==(24 if board=='classic-24' else 20),(label,initial)
 assert initial['docW']<=width+2,(label,initial)
 assert initial['imagesLoaded'],(label,initial)
 assert initial['firstPrimary'] is None or initial['firstPrimary']['h']>=44,(label,initial)
 if url!=PUBLIC:
  assert not initial['under44Active'],(label,'candidate touch targets under 44px',initial['under44Active'])
 firstshot=screenshot(page,f'{label}-playing')
 frames=sample_frames(page)
 page.wait_for_function("document.querySelector('main')?.dataset.gameStatus==='finished'",timeout=95000)
 wall=round((time.monotonic()-start)*1000)
 if audioStress:
  page.wait_for_function("window.__releaseOscStart>0&&window.__releaseOscStart===window.__releaseOscEnd",timeout=10000)
 end=identity(page);after=metrics(page)
 finalshot=screenshot(page,f'{label}-finished')
 revision=int(page.locator('main').get_attribute('data-game-revision'))
 assets=page.locator('.asset-quick-roster').inner_text()
 saved_at=None
 page.wait_for_function("""async expected=>{
   const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('reactmono-local-saves',1);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});
   const row=await new Promise(resolve=>{const r=db.transaction('slots','readonly').objectStore('slots').get('auto');r.onsuccess=()=>resolve(r.result)});
   db.close();return row&&JSON.parse(row.contents).game.revision===expected;
 }""",arg=revision,timeout=30000)
 saved_at=auto_revision(page)
 assert saved_at==revision,(label,saved_at,revision)
 if offline:
  page.wait_for_function("navigator.serviceWorker.controller!==null",timeout=30000)
  caches=page.evaluate("async()=>await caches.keys()")
  assert len([x for x in caches if x.startswith('reactmono-')])==1,caches
  ctx.set_offline(True);page.reload(wait_until='load',timeout=20000)
  page.wait_for_function("document.querySelectorAll('.save-list li').length>0")
  page.locator('.save-list li').filter(has_text='自动存档').get_by_role('button',name='读取').click()
  page.wait_for_function("(rev)=>document.querySelector('main')?.dataset.gameRevision===rev",arg=str(revision),timeout=20000)
  assert page.locator('.asset-quick-roster').inner_text()==assets
  assert page.locator('main').get_attribute('data-game-status')=='finished'
  screenshot(page,f'{label}-offline-restored')
 assert not errors,(label,errors)
 row={'label':label,'url':url,'map':board,'seats':seats,'viewport':[width,height],
   'setup':setup,'gameStart':initial,'gameFinished':end,'load':start_metrics,
   'finalResources':after,'frames':frames,'completeGameWallMs':wall,
   'revision':revision,'assets':assets,'savedRevision':saved_at,
   'offlineRestored':offline,'firstShot':firstshot,'lastShot':finalshot,'pageErrors':errors}
 ctx.close();return row
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
 thread=Thread(target=server.serve_forever,daemon=True);thread.start()
 rows=[]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
   local=f'http://127.0.0.1:{server.server_port}/ReactMono/'
   # Same runner, same exact seed and 8-round cap. Published build remains prior dev
   # until this PR is merged; label explicitly as public BEFORE vs local CANDIDATE.
   for label,w,h,board,count in SCENARIOS:
    if label in ('desktop-classic-2','phone-classic-4'):
     rows.append(scenario(browser,PUBLIC,'public-before-'+label,w,h,board,count))
    rows.append(scenario(browser,local,'candidate-'+label,w,h,board,count,offline=label in ('phone-classic-4','small-phone-harbor-3')))
   for label in ('desktop-classic-2','phone-classic-4'):
    before=next(x for x in rows if x['label']=='public-before-'+label)
    after=next(x for x in rows if x['label']=='candidate-'+label)
    assert before['revision']==after['revision'],(label,'engine revision mismatch')
    assert before['assets']==after['assets'],(label,'asset mismatch')
    # 44px sound toggle increases phone action-panel height by 4px; board may
    # move down slightly, but must retain its exact intrinsic geometry.
    original=before['gameStart']['board'];candidate=after['gameStart']['board']
    assert all(abs(original[k]-candidate[k])<=2 for k in ('x','w','h')),(label,'board dimensions changed',original,candidate)
    assert abs(original['y']-candidate['y'])<=12,(label,'board displaced',original,candidate)
    assert before['gameStart']['markers']==after['gameStart']['markers'],(label,'character count changed')
   browser.close()
  report={'evidence':'actual Chromium in shared CI; public previous deployment vs local candidate',
   'timingsWarning':'Shared GitHub runner, not a physical phone; wall time is variable',
   'seed':7217,'maxRounds':8,'humanParticipants':0,'scenarios':rows,'comparisonPairs':2,
   'assetBudgetFile':'artifacts/issue72/asset-budgets.json'}
  (OUT/'chromium-metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
  print('PASS #72 real Chromium perf/visual/offline/archive comparison '+json.dumps([
   {'scenario':r['label'],'loadMs':r['load']['pageLoadMs'],'fcpMs':r['load']['fcpMs'],
    'wallMs':r['completeGameWallMs'],'framesP95':r['frames']['p95Ms'],
    'heap':r['finalResources']['usedJsHeapBytes'],'dbWrites':r['finalResources']['indexedDbPuts'],
    'revision':r['revision'],'offline':r['offlineRestored']}
   for r in rows],ensure_ascii=False))
 finally:
  server.shutdown();thread.join()
if __name__=='__main__':main()
