"""P007: inspect real rendered route pixels, canvas navigation and large-map coverage."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
import json,math,time,os,base64,faulthandler
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
     if os.environ.get('WORLD_MAP') and level['map']['id']!=os.environ['WORLD_MAP']:continue
     mid=level['map']['id'];width,height=(390,844) if phone else (1440,900)
     ctx=browser.new_context(viewport={'width':width,'height':height},has_touch=phone,is_mobile=phone,device_scale_factor=2 if phone else 1)
     ctx.add_init_script(METRICS+'''
for(const name of ['drawElementsInstanced','drawArraysInstanced']){const old=WebGL2RenderingContext.prototype[name];WebGL2RenderingContext.prototype[name]=function(...args){window.__metrics.draws++;return old.apply(this,args)}}
''');pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)))
     pg.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
     pg.goto(url);open_new_game_setup(pg);select_map(pg,mid)
     pg.get_by_role('button',name='开始游戏',exact=True).click();shell=pg.locator('.canvas-shell[data-ready=true]');shell.wait_for();pg.wait_for_timeout(700)
     pg.get_by_role('button',name='查看全图',exact=True).click();pg.wait_for_timeout(1700)
     assert shell.get_attribute('data-camera-mode')=='overview'
     frame=base64.b64encode(pg.locator('canvas').screenshot()).decode()
     insets=json.loads(shell.get_attribute('data-camera-insets'))
     zoom=float(shell.get_attribute('data-camera-zoom'));cx,cz=map(float,shell.get_attribute('data-camera-center').split(','))
     sx=(insets['left']+width-insets['right'])/2;sy=(insets['top']+height-insets['bottom'])/2
     hits=0;coords=[]
     for cell in level['map']['cells']:
      x=(cell['column']-(level['map']['columns']+1)/2)*2;z=(cell['row']-(level['map']['rows']+1)/2)*2
      px=sx+((x-cx)-(z-cz))/math.sqrt(2)*zoom
      py=sy+((x-cx)+(z-cz))/math.sqrt(2)*SIN*zoom+.53*math.sqrt(1-SIN*SIN)*zoom
      assert insets['left']-2<px<width-insets['right']+2,(mid,phone,px)
      assert insets['top']-2<py<height-insets['bottom']+2,(mid,phone,py)
      coords.append([px,py])
     colors=pg.evaluate("""async ({frame,coords,width})=>{const response=await fetch('data:image/png;base64,'+frame);const bitmap=await createImageBitmap(await response.blob());const c=document.createElement('canvas');c.width=bitmap.width;c.height=bitmap.height;const ctx=c.getContext('2d');ctx.drawImage(bitmap,0,0);return coords.map(([x,y])=>Array.from(ctx.getImageData(Math.round(x*bitmap.width/width),Math.round(y*bitmap.width/width),1,1).data).slice(0,3));}""",{'frame':frame,'coords':coords,'width':width})
     hits=sum(b>=g-26 for r,g,b in colors)
     pg.screenshot(path=str(OUT/f"{mid}-{'phone' if phone else 'desktop'}-overview.png"))
     assert hits/len(coords)>.94,(mid,phone,'rendered road missing',hits,len(coords))
     label='phone' if phone else 'desktop';pg.screenshot(path=str(OUT/f'{mid}-{label}-overview.png'))
     pg.evaluate('window.__metrics.frames=[];window.__metrics.draws=0');pg.wait_for_timeout(1000)
     metrics=pg.evaluate('window.__metrics');frames=sorted(metrics['frames']);stats=json.loads(shell.get_attribute('data-render-stats'))
     gpu=pg.locator('canvas').evaluate('(c)=>{const g=c.getContext("webgl2"),d=g.getExtension("WEBGL_debug_renderer_info");return g.getParameter(d.UNMASKED_RENDERER_WEBGL)}')
     overview={'zoom':zoom,'roadPixels':hits,'cells':len(coords),'p50':frames[len(frames)//2],'p95':frames[int(len(frames)*.95)],'allPassDrawsPerFrame':metrics['draws']/len(frames),'renderer':stats,'gpu':gpu}
     pg.get_by_role('button',name='定位当前玩家',exact=True).click();pg.wait_for_timeout(1000)
     followZoom=float(shell.get_attribute('data-camera-zoom'));assert followZoom>=20
     assert pg.locator('.camera-toggle').get_attribute('aria-pressed')=='true'
     pg.screenshot(path=str(OUT/f'{mid}-{label}-follow.png'))
     # Wheel changes actual projection; drag changes center but must not select a tile.
     canvas=pg.locator('canvas');pg.mouse.move(sx,sy);pg.mouse.wheel(0,-180);pg.wait_for_timeout(700)
     assert float(shell.get_attribute('data-camera-zoom'))>followZoom
     if phone:
      initial=float(shell.get_attribute('data-camera-zoom'));cdp=ctx.new_cdp_session(pg)
      cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sx-25,'y':sy,'id':1},{'x':sx+25,'y':sy,'id':2}]})
      cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':sx-45,'y':sy,'id':1},{'x':sx+45,'y':sy,'id':2}]})
      cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});pg.wait_for_timeout(650)
      assert float(shell.get_attribute('data-camera-zoom'))>=min(96,initial*1.6)
     old=shell.get_attribute('data-camera-center');pg.mouse.move(sx,sy);pg.mouse.down();pg.mouse.move(sx+95,sy+40,steps=12);pg.mouse.up();pg.wait_for_timeout(600)
     assert shell.get_attribute('data-camera-mode')=='browse' and shell.get_attribute('data-camera-center')!=old
     assert pg.locator('.board-inspector').count()==0
     canvas.focus();pg.keyboard.press('Home');pg.wait_for_timeout(1200);assert shell.get_attribute('data-camera-mode')=='overview'
     if phone:pg.get_by_role('button',name='放大地图',exact=True).click();pg.wait_for_timeout(500)
     # Physical pointer clicks on minimap at a far corner, last tile and a concave section.
     for index in [len(level['map']['route'])//2,len(level['map']['route'])-1,len(level['map']['route'])//3]:
      tile=level['map']['cells'][level['map']['route'][index]]
      x=(tile['column']-(level['map']['columns']+1)/2)*2;z=(tile['row']-(level['map']['rows']+1)/2)*2
      screen=pg.locator('.world-minimap svg').evaluate('(svg,p)=>{const q=new DOMPoint(p.x,p.z).matrixTransform(svg.getScreenCTM());return {x:q.x,y:q.y}}',{'x':x,'z':z})
      # Native MouseEvent client coordinates are integral pixels. At 360 cells,
      # one minimap pixel spans adjacent road cells; verify that physical precision.
      svgBox=pg.locator('.world-minimap svg').bounding_box()
      tolerance=max(.15,1.6*max((level['map']['columns']*2+8)/svgBox['width'],(level['map']['rows']*2+8)/svgBox['height']))
      print('NAV',mid,label,index,[x,z],screen,'from',shell.get_attribute('data-camera-center'),flush=True)
      pg.mouse.click(screen['x'],screen['y']);pg.wait_for_function("([x,z,t])=>{const p=document.querySelector('.canvas-shell').dataset.cameraCenter.split(',').map(Number);return Math.hypot(p[0]-x,p[1]-z)<t}",arg=[x,z,tolerance],timeout=5000)
      assert pg.locator('.camera-toggle').get_attribute('aria-pressed')=='false'
      center=list(map(float,shell.get_attribute('data-camera-center').split(',')));assert math.hypot(center[0]-x,center[1]-z)<tolerance,(mid,index,center,[x,z])
      if index==len(level['map']['route'])//2:pg.screenshot(path=str(OUT/f'{mid}-{label}-far.png'))
     pg.get_by_role('button',name='定位当前玩家',exact=True).click();pg.wait_for_timeout(600)
     pg.evaluate('window.__metrics.frames=[]');pg.get_by_role('button',name='掷骰前进').click()
     pg.wait_for_function('document.querySelector("main").dataset.presenting==="false"',timeout=10000)
     moving=sorted(pg.evaluate('window.__metrics.frames'));assert len(moving)>10
     motionMetrics={'p50':moving[len(moving)//2],'p95':moving[int(len(moving)*.95)],'frames':len(moving)}
     assert shell.get_attribute('data-camera-mode')=='follow'
     report.append({'motion':motionMetrics,'pinch':phone,'map':mid,'viewport':[width,height],'overview':overview,'followZoom':followZoom,'farCorners':True,'wheelDragKeyboard':True})
     print('PASS',mid,label,json.dumps(overview),flush=True);faulthandler.dump_traceback_later(15);pg.goto('about:blank');ctx.close();faulthandler.cancel_dump_traceback_later()
   assert not errors,errors
   print('CLOSING browser',flush=True);faulthandler.dump_traceback_later(15);browser.close()
  faulthandler.cancel_dump_traceback_later()
  (OUT/'acceptance.json').write_text(json.dumps({'results':report,'errors':errors,'physicalPhones':0,'humanParticipants':0},ensure_ascii=False,indent=2))
 finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':main()
