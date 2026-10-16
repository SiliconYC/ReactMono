"""#63 real React/engine interaction, offline art and responsive browser screenshots."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
import json,os

OUT=Path('artifacts/issue63')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    t=Thread(target=server.serve_forever,daemon=True);t.start()
    observations=[];errors=[]
    try:
      with sync_playwright() as pw:
        opts={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
        if os.environ.get('CHROMIUM_PATH'):opts['executable_path']=os.environ['CHROMIUM_PATH']
        else:opts['channel']='chrome'
        browser=pw.chromium.launch(**opts)
        for name,width,height in [('desktop',1440,900),('phone',390,844)]:
          context=browser.new_context(viewport={'width':width,'height':height},
            has_touch=name=='phone',is_mobile=name=='phone',device_scale_factor=1,
            service_workers='allow',reduced_motion='reduce')
          page=context.new_page()
          page.on('pageerror',lambda e:errors.append(str(e)))
          site=f'http://127.0.0.1:{server.server_port}/ReactMono/'
          # Root registration is deliberately reused; the lab must run offline, without a separate SW.
          page.goto(site,wait_until='load')
          assert page.locator('a.visual-lab-link').count()==1
          page.wait_for_function('navigator.serviceWorker.controller!==null',timeout=30000)
          page.goto(site+'visual-lab.html',wait_until='load')
          assert page.get_by_role('heading',name='小镇棋盘').count()==1
          assert page.locator('.v-tile').count()==24
          assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
          assert page.evaluate('[...document.images].every(e=>e.complete&&e.naturalWidth>0)')
          before=page.locator('.v-board').evaluate('(e)=>getComputedStyle(e).backgroundColor')
          page.get_by_role('button',name='糖果霓虹').click()
          after=page.locator('.v-board').evaluate('(e)=>getComputedStyle(e).backgroundColor')
          assert before!=after,{'before':before,'after':after}
          page.get_by_role('button',name='纸艺小镇').click()
          page.locator('.v-tile').nth(1).click()
          assert page.locator('.v-inspector').inner_text().strip()
          page.screenshot(path=str(OUT/f'{name}-paper-classic.png'),full_page=True,animations='disabled')
          page.get_by_label('预览地图').select_option('harbor-20')
          assert page.locator('.v-tile').count()==20
          assert page.locator('main').get_attribute('data-map-id')=='harbor-20'
          page.get_by_role('button',name='掷骰前进 →').click()
          phase=page.locator('main').get_attribute('data-lab-phase')
          assert phase in ('await_decision','await_end_turn','await_shop','await_roll'),phase
          if phase=='await_decision':
            page.get_by_role('button',name='购买地产 '+str(0)).count() # no-op, dynamic price
            page.get_by_role('button',name='放弃购买').click()
            phase=page.locator('main').get_attribute('data-lab-phase')
          if phase=='await_shop':page.get_by_role('button',name='离开商店').click()
          if page.locator('main').get_attribute('data-lab-phase')=='await_end_turn':
            page.get_by_role('button',name='银行存入 50').click()
            assert '已存入 50' in page.get_by_role('status').inner_text()
            page.get_by_role('button',name='结束回合 →').click()
            assert 'p2' not in (page.locator('.v-player[data-active=true]').get_attribute('data-id') or '')
          assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
          page.screenshot(path=str(OUT/f'{name}-harbor-interaction.png'),full_page=True,animations='disabled')
          if name=='phone':
            context.set_offline(True)
            page.reload(wait_until='load')
            assert page.locator('.v-tile').count()==24 or page.locator('.v-tile').count()==20
            assert page.evaluate('[...document.images].every(e=>e.complete&&e.naturalWidth>0)')
            page.get_by_role('button',name='糖果霓虹').click()
            assert page.get_by_role('button',name='糖果霓虹').get_attribute('aria-pressed')=='true'
            page.screenshot(path=str(OUT/'phone-offline-candy.png'),full_page=True,animations='disabled')
          observations.append({'case':name,'viewport':[width,height],'mapSwitched':True,
            'themeSwitched':True,'interactionPhase':phase,'offlineChecked':name=='phone'})
          context.close()
        browser.close()
      assert not errors,errors
      (OUT/'report.json').write_text(json.dumps({'screenshots':5,'tests':observations,'pageErrors':errors,
        'licenseManifest':'dist/art-manifest.json','humanFeedback':False},ensure_ascii=False,indent=2),encoding='utf-8')
      print('PASS #63 original visual system: real React/engine, 2 themes, two maps, desktop/mobile/offline; screenshots=5')
    finally:server.shutdown();t.join()

if __name__=='__main__':main()
