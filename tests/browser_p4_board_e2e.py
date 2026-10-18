"""#64 — real Chromium acceptance of the actual React game boards (not a mockup)."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler, open_new_game_setup, select_map
import json, os, re

OUT=Path('artifacts/issue64')
CASES=[
    ('desktop-classic',1440,900,'classic-24',4,True),
    ('desktop-harbor',1280,800,'harbor-20',4,True),
    ('phone-classic',390,844,'classic-24',4,True),
    ('phone-harbor',390,844,'harbor-20',4,True),
    ('narrow-classic',320,640,'classic-24',4,False),
    ('narrow-harbor',320,640,'harbor-20',4,False),
]

def geometry(page):
    return page.evaluate("""async () => {
      const {DEFAULT_MAP,HARBOR_MAP}=await import('./core/maps.js');
      const board=document.querySelector('.board');
      const map=board.dataset.boardTheme==='harbor-20'?HARBOR_MAP:DEFAULT_MAP;
      const tiles=[...board.querySelectorAll('.tile')];
      const rect=e=>{const r=e.getBoundingClientRect();return {
        left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};
      const positions=tiles.map(t=>({id:Number(t.dataset.tileId),
        column:Number(getComputedStyle(t).gridColumnStart),
        row:Number(getComputedStyle(t).gridRowStart),rect:rect(t)}));
      const bad=positions.filter((p,i)=>p.id!==i||p.column!==map.cells[i].column||
        p.row!==map.cells[i].row);
      const overlaps=positions.some((a,i)=>positions.some((b,j)=>i!==j&&
        Math.max(a.rect.left,b.rect.left)<Math.min(a.rect.right,b.rect.right)-1&&
        Math.max(a.rect.top,b.rect.top)<Math.min(a.rect.bottom,b.rect.bottom)-1));
      const pieceNodes=[...board.querySelectorAll('.tile[data-tile-id="0"] .piece')];
      const pieces=pieceNodes.map(e=>({seat:e.textContent,rect:rect(e)}));
      const pieceOverlap=pieces.some((a,i)=>pieces.some((b,j)=>i!==j&&
        Math.max(a.rect.left,b.rect.left)<Math.min(a.rect.right,b.rect.right)-.5&&
        Math.max(a.rect.top,b.rect.top)<Math.min(a.rect.bottom,b.rect.bottom)-.5));
      return {mapId:map.id,route:[...map.route],tiles:tiles.length,bad,overlaps,
        pieces:pieces.map(p=>p.seat),pieceOverlap,viewport:innerWidth,
        documentWidth:document.documentElement.scrollWidth,
        board:rect(board),viewportRect:rect(document.querySelector('.board-viewport')),
        scrollable:document.querySelector('.board-viewport').scrollWidth>
          document.querySelector('.board-viewport').clientWidth,
        artwork:tiles.every(t=>t.querySelector('.tile-artwork')!==null),
        selected:tiles.filter(t=>t.getAttribute('aria-pressed')==='true').length};
    }""")

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    observations=[];errors=[]
    try:
      with sync_playwright() as pw:
        opts={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
        if os.environ.get('CHROMIUM_PATH'):opts['executable_path']=os.environ['CHROMIUM_PATH']
        else:opts['channel']='chrome'
        browser=pw.chromium.launch(**opts)
        for name,width,height,map_id,seats,special in CASES:
          context=browser.new_context(viewport={'width':width,'height':height},
            device_scale_factor=1,is_mobile=width<=390,has_touch=width<=390,
            reduced_motion='reduce',service_workers='allow')
          page=context.new_page()
          page.on('pageerror',lambda e:errors.append(str(e)))
          page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/',wait_until='load')
          open_new_game_setup(page)
          assert page.locator('link[href="./board-art.css"]').count()==1
          select_map(page,map_id)
          page.get_by_label('玩家人数').select_option(str(seats))
          page.get_by_label('对局种子').fill('17')
          page.get_by_label('最多轮数').fill('3')
          for index in range(seats):
            page.get_by_label(f'第 {index+1} 位玩家类型').select_option('human')
          if special:page.get_by_label('启用医院、监狱与商店').check()
          page.screenshot(path=str(OUT/f'{name}-setup.png'),full_page=True,animations='disabled')
          page.get_by_role('button',name=re.compile('开始游戏')).click()
          report=geometry(page)
          assert report['mapId']==map_id and report['tiles']==(24 if map_id=='classic-24' else 20),report
          assert not report['bad'] and not report['overlaps'],report
          assert not report['pieceOverlap'] and report['pieces']==['1','2','3','4'],report
          assert report['artwork'] and report['selected']==1,report
          assert report['viewport']<=width+2 and report['documentWidth']<=width+2,report
          if width==320:assert report['scrollable'],report
          else:assert not report['scrollable'],report
          assert page.locator('.tile-current').count()==1
          if special:
            for facility in ['hospital','prison','shop']:
              assert page.locator(f'.tile-art-{facility}').count()==1,facility
          page.locator('.tile[data-tile-id="1"]').click()
          assert page.locator('.tile[data-tile-id="1"]').get_attribute('aria-pressed')=='true'
          assert '1 · ' in page.locator('.board-inspector').inner_text()
          assert page.locator('.board-inspector').inner_text().strip()
          page.screenshot(path=str(OUT/f'{name}-four-players.png'),full_page=True,animations='disabled')
          page.get_by_role('button',name=re.compile('掷骰前进')).click()
          phase=page.locator('main').get_attribute('data-game-phase')
          if phase=='await_decision':
            tile=page.locator('main').evaluate("""e=>Number(e.dataset.gameRevision)""")
            assert tile>0
            page.get_by_role('button',name=re.compile('购买地产')).click()
            assert page.locator('.tile[data-owner-id="p1"]').count()>=1
          if phase=='await_shop':page.get_by_role('button',name=re.compile('离开商店')).click()
          phase=page.locator('main').get_attribute('data-game-phase')
          assert phase in ('await_end_turn','await_roll'),phase
          page.screenshot(path=str(OUT/f'{name}-after-move.png'),full_page=True,animations='disabled')
          if name=='phone-harbor':
            page.wait_for_function('navigator.serviceWorker.controller!==null',timeout=30000)
            context.set_offline(True)
            page.reload(wait_until='load')
            select_map(page,'harbor-20')
            assert page.locator('.tile').count()==20
            assert page.locator('.tile-artwork').count()==page.locator('.tile').count()
            assert page.locator('link[href="./board-art.css"]').count()==1
            assert page.locator('.tile').first.evaluate(
                '(el)=>getComputedStyle(el).getPropertyValue("appearance")')=='none'
            page.screenshot(path=str(OUT/'phone-harbor-offline.png'),full_page=True,animations='disabled')
          observations.append({'case':name,'geometry':report,'phaseAfterRoll':phase,
            'realBrowser':True,'offline':name=='phone-harbor'})
          context.close()
        browser.close()
      assert not errors,errors
      (OUT/'report.json').write_text(json.dumps({
        'origin':'real Chromium, served dist from /ReactMono/',
        'sourceCommit':os.getenv('GITHUB_SHA','local'),
        'humanFeedback':False,'scenarios':observations,'pageErrors':errors
      },ensure_ascii=False,indent=2),encoding='utf-8')
      print('PASS #64: 6 real desktop/phone boards, 4 unique seats, exact map coordinates, click/roll/economy, PWA; screenshots=19')
    finally:server.shutdown();thread.join()

if __name__=='__main__':run()
