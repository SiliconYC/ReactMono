"""Real production save import: upgraded large-town LOD, memory and frame samples."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
import json
import faulthandler
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
from browser_main_game_acceptance import (
    fixture, load_fixture, 设置地图视角,
)
from browser_main_runtime_e2e import METRICS
OUT=Path('artifacts/scalable-world');OUT.mkdir(parents=True,exist_ok=True)

def main():
 faulthandler.dump_traceback_later(30,repeat=True)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start();url=f'http://127.0.0.1:{server.server_port}/ReactMono/'
 report=[];errors=[]
 try:
  raw=fixture("const {levelConfig}=await import('./.test-dist/core/level-data.js');game=act(createGame(17,{...cfg,...levelConfig('ridges-360'),players:cfg.players,maxRounds:60}),'start_game');game={...game,players:game.players.map((p,i)=>({...p,position:i===0?120:0})),tiles:game.tiles.map(t=>t.kind==='property'?{...t,ownerId:'p1',level:2}:t)};")
  with sync_playwright() as p:
   browser=p.chromium.launch(channel='chrome',headless=True)
   for phone in [False,True]:
    ctx=browser.new_context(viewport={'width':390 if phone else 1440,'height':844 if phone else 900},device_scale_factor=2 if phone else 1)
    ctx.add_init_script(METRICS+";for(const name of ['drawElementsInstanced','drawArraysInstanced']){const old=WebGL2RenderingContext.prototype[name];WebGL2RenderingContext.prototype[name]=function(...args){window.__metrics.draws++;return old.apply(this,args)}}")
    pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    load_fixture(pg,url,raw,'满建城镇压力存档');shell=pg.locator('.canvas-shell[data-ready=true]')
    near=[]
    for cycle in range(4):
     for mode,button in [('follow','定位当前玩家'),('overview','查看全图')]:
      设置地图视角(pg, mode);pg.wait_for_timeout(1100)
      print('navigation cycle',phone,cycle,mode,flush=True)
      stats=json.loads(shell.get_attribute('data-render-stats'))
      if mode=='follow':near.append(stats)
      if cycle==0:
       pg.evaluate('window.__metrics.frames=[];window.__metrics.draws=0');pg.wait_for_timeout(1200);metrics=pg.evaluate('window.__metrics');frames=sorted(metrics['frames'])
       report.append({'phone':phone,'mode':mode,'renderer':stats,'allPassDrawsPerFrame':metrics['draws']/len(frames),'p50':frames[len(frames)//2],'p95':frames[int(len(frames)*.95)]})
       pg.screenshot(path=str(OUT/f'ridges-360-built-save-{"phone" if phone else "desktop"}-{mode}.png'))
    assert near[-1]['textures']==near[0]['textures'],near
    assert near[-1]['geometries']<=near[0]['geometries']+8,near
    report.append({'phone':phone,'navigationCycles':4,'nearMemory':near})
    print('closing context',phone,flush=True);pg.goto('about:blank');ctx.close();print('closed context',phone,flush=True)
   assert not errors,errors
   browser.close()
  (OUT/'populated.json').write_text(json.dumps({'results':report,'errors':errors,'fixture':'规则生成并通过正式存档导入的360格满建压力对局；不冒充自然养成进度','physicalPhones':0},ensure_ascii=False,indent=2));print('PASS populated large-town rendering, stable navigation memory',json.dumps(report),flush=True)
 finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':main()
