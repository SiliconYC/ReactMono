"""#65 real Chromium acceptance: four original seat identities on both working maps, offline and saves."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
import json, os, re

OUT=Path('artifacts/issue65')
CASES=[
  ('desktop-harbor-mixed',1440,900,'harbor-20',4,(1,3)),
  ('phone-classic-human',390,844,'classic-24',4,()),
  ('narrow-harbor',320,640,'harbor-20',2,()),
  ('desktop-classic',1280,800,'classic-24',4,()),
]
NAMES=['fox','bear','rabbit','bird']

def inspect(page, seats):
    result=page.evaluate("""() => {
      const nodes=[...document.querySelectorAll('.tile[data-tile-id="0"] .piece')];
      const portraits=[...document.querySelectorAll('.asset-player .character-badge')];
      const boxes=nodes.map(e=>{const r=e.getBoundingClientRect();return {
        left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}});
      const collisions=boxes.some((a,i)=>boxes.some((b,j)=>i!==j&&
        Math.max(a.left,b.left)<Math.min(a.right,b.right)-.5&&
        Math.max(a.top,b.top)<Math.min(a.bottom,b.bottom)-.5));
      return {ids:nodes.map(n=>n.dataset.characterId),
        seats:nodes.map(n=>n.dataset.characterSeat),
        names:nodes.map(n=>n.textContent.trim()),
        roleImages:[...document.querySelectorAll('.character-image')].map(n=>({
          src:n.getAttribute('src'),loaded:n.complete&&n.naturalWidth>0})),
        assetIds:portraits.map(p=>p.dataset.characterId),
        assetSeating:portraits.map(p=>p.dataset.characterSeat),
        collision:collisions,minPawnSize:Math.min(...boxes.map(b=>b.width)),
        horizontalOverflow:document.documentElement.scrollWidth>innerWidth+2};
    }""")
    assert result['ids']==NAMES[:seats],result
    assert result['names']==[str(i) for i in range(1,seats+1)],result
    assert result['seats']==[str(i) for i in range(1,seats+1)],result
    assert result['assetIds']==NAMES[:seats],result
    assert result['assetSeating']==result['seats'],result
    assert not result['collision'] and not result['horizontalOverflow'],result
    assert result['minPawnSize']>=12,result
    assert result['roleImages'] and all(i['loaded'] for i in result['roleImages']),result
    return result

def main():
  OUT.mkdir(parents=True,exist_ok=True)
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
  thread=Thread(target=server.serve_forever,daemon=True);thread.start()
  reports=[];errors=[]
  try:
    with sync_playwright() as pw:
      args={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
      if os.environ.get('CHROMIUM_PATH'):args['executable_path']=os.environ['CHROMIUM_PATH']
      else:args['channel']='chrome'
      browser=pw.chromium.launch(**args)
      for name,width,height,map_id,seats,computers in CASES:
        context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,
          is_mobile=width<=390,has_touch=width<=390,reduced_motion='reduce',service_workers='allow')
        page=context.new_page()
        page.on('pageerror',lambda err:errors.append(str(err)))
        url=f'http://127.0.0.1:{server.server_port}/ReactMono/'
        page.goto(url,wait_until='load')
        assert page.locator('link[href="./characters.css"]').count()==1
        page.get_by_label('游戏地图').select_option(map_id)
        page.get_by_label('玩家人数').select_option(str(seats))
        page.get_by_label('对局种子').fill('17')
        page.get_by_label('最多轮数').fill('3')
        for i in range(seats):
          page.get_by_label(f'第 {i+1} 位玩家姓名').fill(f'测试者{i+1}')
          page.get_by_label(f'第 {i+1} 位玩家类型').select_option('computer' if i in computers else 'human')
        setup=page.locator('.setup-player .character-setup')
        assert setup.count()==seats
        assert setup.evaluate_all("(xs)=>xs.map(x=>x.dataset.characterSeat)")==[str(i+1) for i in range(seats)]
        assert setup.evaluate_all("(xs)=>xs.map(x=>x.dataset.characterId)")==NAMES[:seats]
        page.screenshot(path=str(OUT/f'{name}-setup.png'),full_page=True,animations='disabled')
        page.get_by_role('button',name=re.compile('开始游戏')).click()
        # React commits synchronously, but freshly mounted same-origin SVGs finish
        # loading asynchronously. Wait for genuine successful loads, not just 'complete'.
        page.wait_for_function("""() => {
          const imgs=[...document.querySelectorAll('.character-image')];
          return imgs.length>0&&imgs.every(img=>img.complete&&img.naturalWidth>0);
        }""",timeout=15000)
        report=inspect(page,seats)
        assert page.locator('.turn-person .character-portrait').get_attribute('data-character-id')=='fox'
        assert page.locator('.asset-player').count()==seats
        for i in range(seats):
          marker=page.locator(f'.asset-player[data-player-id="p{i+1}"] .character-badge')
          assert marker.get_attribute('data-character-id')==NAMES[i]
          assert marker.get_attribute('title').endswith('电脑' if i in computers else '真人')
        page.screenshot(path=str(OUT/f'{name}-four-seats.png'),full_page=True,animations='disabled')
        # Roll goes through the real rules, and the pawn's active landing reflects the resulting tile.
        page.get_by_role('button',name=re.compile('掷骰前进')).click()
        active=page.locator('.pawn-holder[data-player-id="p1"] .piece')
        assert active.count()==1
        moved=active.locator('xpath=ancestor::button')
        tile=int(moved.get_attribute('data-tile-id'))
        assert tile!=0
        assert f'位置：{tile} 号格' in page.locator('.turn-position').inner_text()
        assert active.get_attribute('data-character-id')=='fox'
        assert 'character-moving' in (active.get_attribute('class') or '')
        if page.locator('main').get_attribute('data-game-phase')=='await_decision':
          page.get_by_role('button',name=re.compile('购买地产')).click()
        if page.locator('main').get_attribute('data-game-phase')=='await_shop':
          page.get_by_role('button',name=re.compile('离开商店')).click()
        page.screenshot(path=str(OUT/f'{name}-landing.png'),full_page=True,animations='disabled')
        if name=='desktop-classic':
          # Complete a short genuine four-human game and verify winner portrait matches seat.
          finished=page.evaluate("""async()=>{
            const click=text=>{
              const el=[...document.querySelectorAll('button')].find(b=>!b.disabled&&b.textContent.includes(text));
              if(!el)return false;el.click();return true;};
            for(let i=0;i<500;i++){
              if(document.querySelector('main')?.dataset.gameStatus==='finished')return true;
              if(click('我已就位，开始操作')){}
              else if(click('跳过当前停留回合')){}
              else if(click('离开商店')){}
              else if(click('掷骰前进')){}
              else if(click('购买地产')){}
              else if(click('放弃购买')){}
              else click('结束当前回合');
              await new Promise(r=>setTimeout(r,20));
            }
            return false;
          }""")
          assert finished
          winner=page.locator('.result-box .character-winner')
          outcome=page.locator('.result-box strong').first.inner_text()
          if '平局' not in outcome:
            assert winner.count()==1
            seat=int(winner.get_attribute('data-character-seat'))
            assert outcome.startswith(f'测试者{seat}'),(seat,outcome)
            assert winner.get_attribute('data-character-id')==NAMES[seat-1]
          else:assert winner.count()==0
          page.screenshot(path=str(OUT/'desktop-classic-finished.png'),full_page=True,animations='disabled')
        if name=='phone-classic-human':
          # Manual save of all 4 IDs; survives reload, roles and visual identity remain stable.
          page.on('dialog',lambda d:d.accept('角色四人续局' if d.type=='prompt' else None))
          page.get_by_role('button',name='创建手动存档').click()
          page.locator('.save-list').get_by_text('角色四人续局').wait_for()
          page.get_by_role('button',name=re.compile('结束当前回合')).click()
          hand=page.locator('.handoff-identity .character-portrait')
          assert hand.get_attribute('data-character-id')=='bear'
          page.screenshot(path=str(OUT/'phone-classic-handoff.png'),full_page=True,animations='disabled')
          page.get_by_role('button',name='我已就位，开始操作').click()
          assert page.locator('.turn-person .character-portrait').get_attribute('data-character-id')=='bear'
          page.reload(wait_until='load')
          page.locator('.save-list').get_by_text('角色四人续局').wait_for()
          page.locator('.save-list li').filter(has_text='角色四人续局').get_by_role('button',name='读取').click()
          page.wait_for_function("document.querySelector('main')?.dataset.gameStatus==='playing'")
          assert page.locator('.turn-person .character-portrait').get_attribute('data-character-id')=='fox'
          assert page.locator('.asset-player .character-badge').evaluate_all(
            "(xs)=>xs.map(x=>x.dataset.characterId)")==NAMES
          page.screenshot(path=str(OUT/'phone-classic-restored.png'),full_page=True,animations='disabled')
          page.wait_for_function('navigator.serviceWorker.controller!==null',timeout=30000)
          context.set_offline(True)
          page.reload(wait_until='load')
          page.wait_for_function("""() => {
            const imgs=[...document.querySelectorAll('.character-image')];
            return imgs.length>=2&&imgs.every(img=>img.complete&&img.naturalWidth>0);
          }""",timeout=15000)
          assert page.locator('.character-image').count()>=2
          assert page.locator('.character-image').evaluate_all(
            "(xs)=>xs.every(e=>e.complete&&e.naturalWidth>0)")
          assert page.locator('link[href="./characters.css"]').count()==1
          page.screenshot(path=str(OUT/'phone-classic-offline.png'),full_page=True,animations='disabled')
        reports.append({'name':name,'seats':seats,'computerSeats':[i+1 for i in computers],
                        'map':map_id,'geometry':report,'landingTile':tile,
                        'offlineChecked':name=='phone-classic-human'})
        context.close()
      browser.close()
    assert not errors,errors
    (OUT/'report.json').write_text(json.dumps({'browser':'real Chromium /ReactMono/ dist',
      'commit':os.environ.get('GITHUB_SHA','local'),'source':'React game, not mockup',
      'humanFeedbackCollected':False,'results':reports,'pageErrors':errors},
      ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS #65: four original identity silhouettes, setup/board/turn/handoff/saves/offline; cases=',len(reports))
  finally:
    server.shutdown();thread.join()

if __name__=='__main__':main()
