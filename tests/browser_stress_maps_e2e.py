"""JSON 关卡经生产 bundle 真正选图、开局、掷骰和存档往返；保留背景现状。"""
from http.server import ThreadingHTTPServer
from threading import Thread
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler, open_new_game_setup, open_saved_games
import json
import re
import os

ROOT=Path(__file__).resolve().parents[1]

def exercise(browser,url,level,phone=False):
    page=browser.new_page(viewport={'width':390 if phone else 1440,'height':844 if phone else 900})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(url,wait_until='networkidle')
    open_new_game_setup(page)
    card=page.locator(f'.setup-map-choice button[data-map-id="{level["map"]["id"]}"]')
    assert card.count()==1, f'缺少数据关卡选项：{level["map"]["id"]}'
    page.get_by_label('最多轮数').fill('7')
    card.click()
    assert page.get_by_label('最多轮数').input_value()==str(level['maxRounds'])
    assert card.get_attribute('aria-pressed')=='true'
    assert card.locator('polyline').count()==1
    assert len(card.locator('polyline').get_attribute('points').split())==len(level['map']['route'])+1
    out=Path(os.environ.get('MAP_SCREENSHOTS',str(ROOT/'artifacts/stress-maps')));out.mkdir(parents=True,exist_ok=True)
    if level['map']['id']=='ridges-360':
        page.screenshot(path=str(out/('selection-phone.png' if phone else 'selection-desktop.png')))
    page.get_by_label('最多轮数').fill('2')
    page.get_by_label('快速模式').check()
    page.get_by_role('button',name=re.compile('开始游戏')).click()
    page.wait_for_function("document.querySelector('main')?.dataset.gameStatus==='playing'")
    assert page.locator('main').get_attribute('data-map-id')==level['map']['id']
    page.locator('.canvas-shell[data-ready="true"]').wait_for()
    if len(level['tiles'])>=60:
        page.screenshot(path=str(out/f'{level["map"]["id"]}-{"phone" if phone else "desktop"}.png'))
    page.get_by_role('button',name=re.compile('掷骰前进')).click()
    # Wait until the first real die/move and decision are resolved, without inspecting React internals.
    page.wait_for_function("document.querySelector('main')?.dataset.presenting==='false' && [...document.querySelectorAll('button')].some(b=>!b.disabled && /购买地产|暂不购买|暂不建设|管理资产|继续下一位|离开商店/.test(b.textContent))")
    save_name='压力图-'+level['map']['id']
    page.on('dialog',lambda d:d.accept(save_name if d.type=='prompt' else None))
    open_saved_games(page)
    page.get_by_role('button',name='创建手动存档').click()
    page.locator('.save-list li').filter(has_text=save_name).wait_for()
    row=page.locator('.save-list li').filter(has_text=save_name)
    with page.expect_download() as downloaded:
        row.get_by_role('button',name='导出',exact=True).click()
    payload=json.loads(Path(downloaded.value.path()).read_text())['game']
    assert payload['map']==level['map']
    assert len(payload['tiles'])==len(level['tiles'])
    assert payload['players'][0]['position']>0
    page.reload(wait_until='networkidle')
    open_saved_games(page)
    page.locator('.save-list li').filter(has_text=save_name).get_by_role('button',name='读取').click()
    page.wait_for_function("document.querySelector('main')?.dataset.gameStatus==='playing'")
    assert page.locator('main').get_attribute('data-map-id')==level['map']['id']
    assert level['name'] in page.locator('.game-place').inner_text()
    if level['map']['id']=='ridges-360' and not phone:
        page.evaluate('navigator.serviceWorker.ready')
        page.context.set_offline(True)
        page.reload(wait_until='load')
        open_saved_games(page)
        page.locator('.save-list li').filter(has_text=save_name).get_by_role('button',name='读取').click()
        page.wait_for_function("document.querySelector('main')?.dataset.gameStatus==='playing'")
        assert page.locator('main').get_attribute('data-map-id')==level['map']['id']

    page.locator('.canvas-shell[data-ready="true"]').wait_for()
    # Finish a short game through real actions, exercising AI as well as the human turn.
    report=page.evaluate("""async()=>{
      const pause=()=>new Promise(r=>setTimeout(r,30));let rolls=0;
      for(let i=0;i<6000;i++){
        if(document.querySelector('main')?.dataset.gameStatus==='finished')return {finished:true,rolls};
        const buttons=[...document.querySelectorAll('button')].filter(b=>!b.disabled&&b.getClientRects().length);
        const pick=patterns=>buttons.find(b=>patterns.some(p=>b.textContent.includes(p)));
        const b=pick(['我已就位','掷骰前进','暂不购买','放弃购买','继续下一位','暂不建设','离开商店','确认操作']);
        if(b){if(b.textContent.includes('掷骰前进'))rolls++;b.click();}
        await pause();
      }return {finished:false,rolls};
    }""")
    assert report['finished'] and report['rolls']>0,report
    assert not errors,errors
    print('PASS',level['map']['id'],len(level['tiles']),'手机' if phone else '桌面','选图/掷骰/存读档/完整短局',report,flush=True)
    page.close()

def main():
    catalog=json.loads((ROOT/'src/data/levels.json').read_text())
    levels=[x for x in catalog['levels'] if x['playable']]
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            for level in levels:
                exercise(browser,f'http://127.0.0.1:{server.server_port}/ReactMono/',level,False)
            exercise(browser,f'http://127.0.0.1:{server.server_port}/ReactMono/',next(level for level in levels if level['map']['id']=='ridges-360'),True)
            browser.close()
    finally:server.shutdown();thread.join()

if __name__=='__main__':main()
