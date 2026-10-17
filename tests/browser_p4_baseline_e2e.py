"""#62 P4 browser experience baseline. Actual Chromium, not DOM mocks or human feedback.
Run after npm run build; screenshots/measurements are retained as CI artifacts.
"""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
import json, os, re, time

OUT=Path('artifacts/issue62')
PUBLIC='https://siliconyc.github.io/ReactMono/'

def capture(page, name, phase):
    report=page.evaluate("""() => {
      const q=s=>document.querySelector(s);
      const r=s=>{const e=q(s);if(!e)return null;const b=e.getBoundingClientRect();return {
        x:Math.round(b.x),y:Math.round(b.y),width:Math.round(b.width),height:Math.round(b.height)}};
      const buttons=[...document.querySelectorAll('button')].filter(e=>!e.disabled);
      const visible=buttons.filter(e=>{const b=e.getBoundingClientRect();return b.width>0&&b.height>0});
      const inViewport=visible.filter(e=>{const b=e.getBoundingClientRect();return b.top>=0&&b.bottom<=innerHeight});
      const tiles=[...document.querySelectorAll('.tile')];
      const sizes=tiles.map(e=>{const b=e.getBoundingClientRect();return {width:Math.round(b.width),height:Math.round(b.height)}});
      return {viewport:{width:innerWidth,height:innerHeight},document:{
        width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight},
        map:q('main')?.dataset.mapId,gameStatus:q('main')?.dataset.gameStatus,
        phase:q('main')?.dataset.gamePhase,tiles:tiles.length,tileMinWidth:Math.min(...sizes.map(t=>t.width)),
        tileMinHeight:Math.min(...sizes.map(t=>t.height)),
        under44px:visible.filter(e=>{const b=e.getBoundingClientRect();return b.height<44}).length,
        buttons:visible.length,buttonsInInitialViewport:inViewport.length,
        primaryCta:r('.turn-card .primary-btn:not([disabled])'),board:r('.board'),assetOverview:r('.asset-overview'),
        sidebar:r('.sidebar'),bank:r('#bank-actions'),loan:r('#loan-actions'),stocks:r('#stock-actions'),
        navTiming:performance.getEntriesByType('navigation').map(n=>({
          duration:Math.round(n.duration),domContentLoaded:Math.round(n.domContentLoadedEventEnd),
          transferSize:n.transferSize}))};
    }""")
    report['scenario']=name
    report['checkpoint']=phase
    path=OUT/f'{name}-{phase}.png'
    page.screenshot(path=str(path),full_page=True,animations='disabled')
    report['screenshot']=str(path)
    assert report['document']['width']<=report['viewport']['width']+2,report
    assert report['tiles'] in (20,24),report
    return report

def run_short_game(page, limit=950):
    return page.evaluate("""async limit=>{
      const click=s=>{const el=[...document.querySelectorAll('button')]
        .find(b=>!b.disabled&&b.textContent.includes(s));if(!el)return false;el.click();return true;};
      let rolls=0,handoffs=0,turns=0,actions=0;
      const t=performance.now();
      for(let i=0;i<limit;i++){
        if(document.querySelector('main')?.dataset.gameStatus==='finished')
          return {finished:true,rolls,handoffs,turns,actions,elapsedMs:Math.round(performance.now()-t)};
        if(click('我已就位'))handoffs++;
        else if(click('跳过当前停留回合')){}
        else if(click('离开商店')){}
        else if(click('掷骰前进'))rolls++;
        else if(click('购买地产')){}
        else if(click('放弃购买')){}
        else if(click('结束当前回合'))turns++;
        actions++;
        await new Promise(r=>setTimeout(r,25));
      }
      return {finished:false,rolls,handoffs,turns,actions,elapsedMs:Math.round(performance.now()-t)};
    }""",limit)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    srv=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=srv.serve_forever,daemon=True)
    thread.start()
    reports=[]
    errors=[]
    try:
      with sync_playwright() as p:
        opts={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
        if os.environ.get('CHROMIUM_PATH'):opts['executable_path']=os.environ['CHROMIUM_PATH']
        else:opts['channel']='chrome'
        browser=p.chromium.launch(**opts)
        for name,width,height,map_id,count,humans in [
          ('desktop-classic-2',1440,900,'classic-24',2,1),
          ('desktop-harbor-4',1280,800,'harbor-20',4,4),
          ('phone-classic-2',390,844,'classic-24',2,2),
          ('phone-harbor-4',390,844,'harbor-20',4,4),
          ('small-phone-portrait',320,640,'classic-24',2,2),
          ('phone-landscape',667,375,'harbor-20',2,2),
        ]:
          context=browser.new_context(viewport={'width':width,'height':height},
              is_mobile=width<=390,has_touch=width<=390,device_scale_factor=1,
              reduced_motion='reduce',service_workers='allow')
          page=context.new_page()
          page.on('pageerror',lambda err:errors.append(str(err)))
          page.goto(f'http://127.0.0.1:{srv.server_port}/ReactMono/',wait_until='load')
          page.get_by_label('游戏地图').select_option(map_id)
          page.get_by_label('玩家人数').select_option(str(count))
          page.get_by_label('对局种子').fill('17')
          page.get_by_label('最多轮数').fill('2')
          page.get_by_label('快速模式').check()
          for i in range(humans):page.get_by_label(f'第 {i+1} 位玩家类型').select_option('human')
          reports.append(capture(page,name,'setup'))
          page.get_by_role('button',name=re.compile('开始游戏')).click()
          assert page.locator('.asset-player').count()==count
          reports.append(capture(page,name,'playing'))
          if name in ('desktop-classic-2','phone-harbor-4'):
            page.get_by_role('button',name=re.compile('掷骰前进')).click()
            if page.locator('main').get_attribute('data-game-phase')=='await_decision':
              page.get_by_role('button',name=re.compile('购买地产|放弃购买')).first.click()
            reports.append(capture(page,name,'decision'))
            if page.locator('main').get_attribute('data-game-phase')=='await_end_turn':
              page.get_by_role('button',name='银行',exact=True).click()
              assert page.get_by_label('银行交易金额').count()==1
              page.get_by_role('button',name='股票',exact=True).click()
              assert page.get_by_label('股票交易数量').count()==1
            result=run_short_game(page)
            assert result['finished'],(name,result)
            if name=='phone-harbor-4':assert result['handoffs']>=3,result
            reports.append({'scenario':name,'checkpoint':'finished','game':result})
            reports.append(capture(page,name,'finished'))
          context.close()
        # Public site check: capture a real published site, do not label it the candidate branch.
        context=browser.new_context(viewport={'width':1440,'height':900})
        page=context.new_page()
        try:
          response=page.goto(PUBLIC,wait_until='load',timeout=30000)
          assert response and response.status==200
          reports.append(capture(page,'public-p3-reference','setup'))
        finally:context.close()
        browser.close()
      assert not errors,errors
      (OUT/'measurements.json').write_text(json.dumps({
        'source':'Real Chromium, local dist served under /ReactMono/ plus current public P3',
        'runner':'GitHub Actions or local installed Chrome','commit':os.getenv('GITHUB_SHA','unknown'),
        'playerFeedbackCollected':False,'reports':reports,'pageErrors':errors
      },ensure_ascii=False,indent=2),encoding='utf-8')
      print('PASS #62 Chromium P4 baseline: 6 viewport/map/seating scenarios, 2 full games, screenshots, public P3 reference; records=',len(reports))
    finally:
      srv.shutdown();thread.join()

if __name__=='__main__':main()
