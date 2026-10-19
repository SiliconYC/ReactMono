"""P007: inspect real rendered route pixels, canvas navigation and large-map coverage."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
import json,math,time,os,base64
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler,open_new_game_setup,select_map
from browser_main_runtime_e2e import METRICS

OUT=Path('artifacts/scalable-world');OUT.mkdir(parents=True,exist_ok=True)
LEVELS=[l for l in json.loads(Path('src/data/levels.json').read_text())['levels'] if not l['map']['id'].startswith('internal-')]
SIN=math.sin(math.atan2(12.2,math.hypot(10.2,10.2)))

def main():
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
 url=f'http://127.0.0.1:{server.server_port}/ReactMono/'
 errors=[];report=[]
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(channel='chrome',headless=True)
   for phone in [False,True]:
    for level in LEVELS:
     mid=level['map']['id'];width,height=(390,844) if phone else (1440,900)
     ctx=browser.new_context(viewport={'width':width,'height':height},has_touch=phone,is_mobile=phone)
     ctx.add_init_script(METRICS);pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)))
     pg.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
     pg.goto(url);open_new_game_setup(pg);select_map(pg,mid)
     pg.get_by_role('button',name='开始游戏',exact=True).click();shell=pg.locator('.canvas-shell[data-ready=true]');shell.wait_for();pg.wait_for_timeout(700)
     pg.get_by_role('button',name='查看全图',exact=True).click();pg.wait_for_timeout(1700)
     assert shell.get_attribute('data-camera-mode')=='overview'
     frame=base64.b64encode(pg.locator('canvas').screenshot()).decode()
     insets=json.loads(shell.get_attribute('data-safe-insets'));insets['right']=max(insets['right'],132 if phone else 202)
     zoom=float(shell.get_attribute('data-camera-zoom'));cx,cz=map(float,shell.get_attribute('data-camera-center').split(','))
     sx=(insets['left']+width-insets['right'])/2;sy=(insets['top']+height-insets['bottom'])/2
     hits=0;coords=[]
     for cell in level['map']['cells']:
      x=(cell['column']-(level['map']['columns']+1)/2)*2;z=(cell['row']-(level['map']['rows']+1)/2)*2
      px=sx+((x-cx)-(z-cz))/math.sqrt(2)*zoom
      py=sy+((x-cx)+(z-cz))/math.sqrt(2)*SIN*zoom+.53*math.sqrt(1-SIN*SIN)*zoom
      assert insets['left']-2<px<width-insets['right']+2,(mid,phone,px)
      assert insets['top']-2<py<height-insets['bottom']+2,(mid,phone,py)
      coords.append([round(px),round(py)])
     colors=pg.evaluate("""async ({frame,coords})=>{const response=await fetch('data:image/png;base64,'+frame);const bitmap=await createImageBitmap(await response.blob());const c=document.createElement('canvas');c.width=bitmap.width;c.height=bitmap.height;const ctx=c.getContext('2d');ctx.drawImage(bitmap,0,0);return coords.map(([x,y])=>Array.from(ctx.getImageData(x,y,1,1).data).slice(0,3));}""",{'frame':frame,'coords':coords})
     hits=sum(b>=g-26 for r,g,b in colors)
     assert hits/len(coords)>.94,(mid,phone,'rendered road missing',hits,len(coords))
     label='phone' if phone else 'desktop';pg.screenshot(path=str(OUT/f'{mid}-{label}-overview.png'))
     pg.evaluate('window.__metrics.frames=[];window.__metrics.draws=0');pg.wait_for_timeout(1000)
     metrics=pg.evaluate('window.__metrics');frames=sorted(metrics['frames']);stats=json.loads(shell.get_attribute('data-render-stats'))
     gpu=pg.locator('canvas').evaluate('(c)=>{const g=c.getContext("webgl2"),d=g.getExtension("WEBGL_debug_renderer_info");return g.getParameter(d.UNMASKED_RENDERER_WEBGL)}')
     overview={'zoom':zoom,'roadPixels':hits,'cells':len(coords),'p50':frames[len(frames)//2],'p95':frames[int(len(frames)*.95)],'allPassDrawsPerFrame':metrics['draws']/len(frames),'renderer':stats,'gpu':gpu}
     pg.get_by_role('button',name='定位当前玩家',exact=True).click();pg.wait_for_timeout(1000)
     followZoom=float(shell.get_attribute('data-camera-zoom'));assert followZoom>=20
     pg.screenshot(path=str(OUT/f'{mid}-{label}-follow.png'))
     # Wheel changes actual projection; drag changes center but must not select a tile.
     canvas=pg.locator('canvas');pg.mouse.move(sx,sy);pg.mouse.wheel(0,-180);pg.wait_for_timeout(700)
     assert float(shell.get_attribute('data-camera-zoom'))>followZoom
     old=shell.get_attribute('data-camera-center');pg.mouse.move(sx,sy);pg.mouse.down();pg.mouse.move(sx+95,sy+40,steps=12);pg.mouse.up();pg.wait_for_timeout(600)
     assert shell.get_attribute('data-camera-mode')=='browse' and shell.get_attribute('data-camera-center')!=old
     assert pg.locator('.board-inspector').count()==0
     canvas.focus();pg.keyboard.press('Home');pg.wait_for_timeout(1200);assert shell.get_attribute('data-camera-mode')=='overview'
     # Physical pointer clicks on minimap at a far corner, last tile and a concave section.
     for index in [len(level['map']['route'])//2,len(level['map']['route'])-1,len(level['map']['route'])//3]:
      tile=level['map']['cells'][level['map']['route'][index]]
      x=(tile['column']-(level['map']['columns']+1)/2)*2;z=(tile['row']-(level['map']['rows']+1)/2)*2
      screen=pg.locator('.world-minimap svg').evaluate('(svg,p)=>{const q=new DOMPoint(p.x,p.z).matrixTransform(svg.getScreenCTM());return {x:q.x,y:q.y}}',{'x':x,'z':z})
      pg.mouse.click(screen['x'],screen['y']);pg.wait_for_timeout(800)
      center=list(map(float,shell.get_attribute('data-camera-center').split(',')));assert math.hypot(center[0]-x,center[1]-z)<.15,(mid,index,center,[x,z])
      if index==len(level['map']['route'])//2:pg.screenshot(path=str(OUT/f'{mid}-{label}-far.png'))
     report.append({'map':mid,'viewport':[width,height],'overview':overview,'followZoom':followZoom,'farCorners':True,'wheelDragKeyboard':True})
     print('PASS',mid,label,json.dumps(overview),flush=True);ctx.close()
   assert not errors,errors
   browser.close()
  (OUT/'acceptance.json').write_text(json.dumps({'results':report,'errors':errors,'physicalPhones':0,'humanParticipants':0},ensure_ascii=False,indent=2))
 finally:server.shutdown();thread.join()
if __name__=='__main__':main()
