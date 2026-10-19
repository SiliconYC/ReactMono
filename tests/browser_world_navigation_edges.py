"""P007 independent navigation regressions: idle GPU, delayed release and end cues."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
import json
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler,open_new_game_setup
from browser_main_runtime_e2e import METRICS
from browser_main_game_acceptance import fixture,load_fixture
OUT=Path('artifacts/scalable-world');OUT.mkdir(parents=True,exist_ok=True)

def main():
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start();url=f'http://127.0.0.1:{server.server_port}/ReactMono/'
 errors=[];passed=[]
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(channel='chrome',headless=True)
   ctx=browser.new_context(viewport={'width':1280,'height':720},reduced_motion='reduce');ctx.add_init_script(METRICS)
   pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)))
   pg.goto(url);open_new_game_setup(pg);pg.get_by_role('button',name='开始游戏',exact=True).click();shell=pg.locator('.canvas-shell[data-ready=true]');shell.wait_for()
   pg.get_by_role('button',name='定位当前玩家',exact=True).click();pg.wait_for_timeout(300)
   assert pg.locator('.camera-toggle').get_attribute('aria-pressed')=='true'
   assert shell.get_attribute('data-frameloop')=='demand'
   startZoom=float(shell.get_attribute('data-camera-zoom'));pg.get_by_role('button',name='放大地图',exact=True).dblclick();pg.wait_for_timeout(150)
   assert float(shell.get_attribute('data-camera-zoom'))>=min(96,startZoom*1.6)
   canvas=pg.locator('canvas');canvas.focus()
   for _ in range(70):pg.keyboard.press('ArrowRight')
   pg.wait_for_timeout(600);before=pg.evaluate('window.__metrics.draws');pg.wait_for_timeout(300);assert pg.evaluate('window.__metrics.draws')==before
   passed.append('减少动态越界后GPU停止绘制')
   pg.get_by_role('button',name='定位当前玩家',exact=True).click();pg.wait_for_timeout(250)
   insets=json.loads(shell.get_attribute('data-safe-insets'));x=(insets['left']+1280-max(insets['right'],202))/2;y=(insets['top']+720-insets['bottom'])/2+20
   pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x+100,y+30,steps=10);pg.wait_for_timeout(650);pg.mouse.up();pg.wait_for_timeout(120)
   assert pg.locator('.board-inspector').count()==0
   assert shell.get_attribute('data-camera-mode')=='browse'
   assert pg.locator('.camera-toggle').get_attribute('aria-pressed')=='false'
   passed.append('拖动按住650ms后松手不误选道路，跟随状态同步')
   # Same live Canvas receives a different registered map through real save UI.
   raw=fixture("const {levelConfig}=await import('./.test-dist/core/level-data.js');game=act(createGame(17,{...cfg,...levelConfig('ridges-360'),players:cfg.players,maxRounds:1}),'start_game');game={...game,players:game.players.map(p=>({...p,position:180}))};game=act(game,'roll');if(game.phase==='await_decision')game=act(game,'decline_property');game=act(game,'end_turn');game=act(game,'roll');if(game.phase==='await_decision')game=act(game,'decline_property');game={...game,players:game.players.map(p=>({...p,cash:2000,bankBalance:0}))};")
   load_fixture(pg,url,raw,'大图平局输入');pg.get_by_role('button',name='定位当前玩家',exact=True).click();pg.wait_for_timeout(200)
   pg.screenshot(path=str(OUT/'cross-map-atlas.png'))
   beforeCenter=shell.get_attribute('data-camera-center');assert beforeCenter!='0.00,0.00'
   if pg.get_by_role('button',name='我已就位，开始操作',exact=True).count():pg.get_by_role('button',name='我已就位，开始操作',exact=True).click()
   pg.get_by_role('button',name='结束当前回合').click();pg.locator('.result-box').wait_for(timeout=7000)
   assert '平局' in pg.locator('.result-box').inner_text()
   assert shell.get_attribute('data-camera-mode')=='overview'
   assert all(abs(float(n))<.1 for n in shell.get_attribute('data-camera-center').split(','))
   pg.screenshot(path=str(OUT/'large-map-draw.png'));passed.append('大图远端平局回到概览，跨图存档保持可用')
   assert not errors,errors
   (OUT/'navigation-edges.json').write_text(json.dumps({'passed':passed,'errors':errors},ensure_ascii=False,indent=2));print('PASS',passed,flush=True);browser.close()
 finally:server.shutdown();thread.join()
if __name__=='__main__':main()
