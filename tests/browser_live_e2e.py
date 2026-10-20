"""P2 的真实同源 HTTP 浏览器回归：直接加载 dist/，不得把 CDN 偷换为测试替身。"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import os
import re
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        clean = path.split('?',1)[0]
        if not clean.startswith('/ReactMono/'):
            return str(ROOT/'dist'/'not-found')
        return str(ROOT/'dist'/clean.removeprefix('/ReactMono/'))
    def log_message(self, *args): pass

def open_new_game_setup(page):
    """Use the real title-to-preparation flow before tests configure a match."""
    title=page.locator('.title-shell[data-setup-screen="title"]')
    if title.count():
        new_game=page.get_by_role('button',name='新游戏')
        if new_game.count(): new_game.click()
        else: page.get_by_role('button',name='开始游戏').click()
    advanced=page.locator('.setup-more')
    if advanced.count() and not advanced.evaluate('(node)=>node.open'):
        advanced.locator('summary').click()

def open_saved_games(page):
    """Open local saves from either the title screen or More menu."""
    if page.locator('.title-shell[data-setup-screen="title"]').count():
        page.get_by_role('button',name='读取存档').click()
        return 'title'
    if page.locator('.game-top').count():
        if page.locator('dialog').count(): page.keyboard.press('Escape')
        page.get_by_role('button',name=re.compile('^菜单')).click()
        page.get_by_role('dialog').get_by_role('button',name=re.compile('^存档')).click()
        return 'game'
    menu=page.locator('.utility-menu')
    if not menu.count(): return 'missing'
    assets=page.locator('.asset-overview')
    if assets.count() and assets.evaluate('(node)=>node.open'):
        assets.evaluate('(node)=>node.open=false')
    if not menu.evaluate('(node)=>node.open'):
        menu.locator(':scope > summary').click()
    saves=page.locator('.saves-card')
    if saves.count() and not saves.evaluate('(node)=>node.open'):
        saves.locator(':scope > summary').click()
    return 'game'

def select_map(page,map_id):
    import json
    levels=json.loads((ROOT/'src/data/levels.json').read_text())['levels']
    label=next(level['name'] for level in levels if level['map']['id']==map_id)
    cards=page.locator('.setup-map-choice button')
    if cards.count():
        cards.filter(has_text=label).click()
    elif page.get_by_label('游戏地图').count():
        page.get_by_label('游戏地图').select_option(map_id)

def main():
    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            launch = {'headless':True, 'args':['--no-sandbox','--disable-dev-shm-usage']}
            if os.environ.get('CHROMIUM_PATH'):
                launch['executable_path'] = os.environ['CHROMIUM_PATH']
            else:
                launch['channel'] = 'chrome'
            browser = p.chromium.launch(**launch)
            page = browser.new_page(viewport={'width':1440,'height':900})
            errors = []
            external = []
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda request:external.append(request.url) if not request.url.startswith('http://127.0.0.1:') else None)
            page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/',wait_until='load')
            open_new_game_setup(page)
            assert page.locator('.setup-map-choice button[data-map-id="classic-24"]').count()==1
            assert page.locator('.setup-map-choice button[data-map-id="harbor-20"]').count()==1
            page.get_by_label('对局种子').fill('17')
            page.get_by_label('快速模式').check()
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            report=page.evaluate("""async()=>{
                const click=s=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes(s)&&!x.disabled);if(!b)return false;b.click();return true};
                const pause=()=>new Promise(r=>setTimeout(r,20));
                let rolls=0,turns=0,buys=0;
                for(let i=0;i<1200;i++){
                    if(document.querySelector('main[data-game-status]')?.dataset.gameStatus==='finished')
                        return {finished:true,rolls,turns,buys};
                    if(click('掷骰前进'))rolls++;
                    else if(click('购买地产'))buys++;
                    else if(click('放弃购买')){}
                    else if(click('结束当前回合'))turns++;
                    await pause();
                }
                return {finished:false,rolls,turns,buys};
            }""")
            assert report['finished'] and report['rolls']>0 and report['turns']>0 and report['buys']>0,report
            assert not errors,errors
            assert not external,external
            print('PASS: /ReactMono/ 同源 React 真实浏览器完整对局',report)
            browser.close()
    finally:
        server.shutdown()
        thread.join()

if __name__=='__main__': main()
