"""通过真实 Chromium IndexedDB 校验多存档、自动保存、刷新续档与删除隔离。"""
import re
from threading import Thread
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler, open_new_game_setup, open_saved_games

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    t=Thread(target=server.serve_forever,daemon=True);t.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page()
            errors=[]
            prompts=iter(['第一份存档','第二份存档'])
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('dialog',lambda dialog:dialog.accept(next(prompts) if dialog.type=='prompt' else None))
            page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
            open_new_game_setup(page)
            page.get_by_label('对局种子').fill('17')
            page.get_by_label('快速模式').check()
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            page.get_by_role('button',name=re.compile('掷骰前进')).click()
            original=page.locator('main').get_attribute('data-game-revision')
            open_saved_games(page)
            page.get_by_role('button',name='创建手动存档').click()
            page.locator('.save-list').get_by_text('第一份存档').wait_for()
            page.get_by_role('button',name='返回标题').click()
            page.get_by_role('button',name='新游戏').click()
            open_new_game_setup(page)
            page.get_by_label('对局种子').fill('23')
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            open_saved_games(page)
            page.get_by_role('button',name='创建手动存档').click()
            page.locator('.save-list').get_by_text('第二份存档').wait_for()
            page.reload()
            open_saved_games(page)
            page.locator('.title-save-list').get_by_text('第一份存档').wait_for()
            assert page.locator('.title-save-list').get_by_text('第二份存档').count()==1
            row=page.locator('.title-save-list li').filter(has_text='第一份存档')
            row.get_by_role('button',name='读取').click()
            page.wait_for_function('(r)=>document.querySelector("main")?.dataset.gameRevision===r',arg=original)
            assert page.locator('main').get_attribute('data-game-revision')==original
            assert page.locator('main').get_attribute('data-game-status')=='playing'
            open_saved_games(page)
            row=page.locator('.save-list li').filter(has_text='第一份存档')
            row.get_by_role('button',name='删除').click()
            page.wait_for_function("!document.querySelector('.save-list')?.textContent.includes('第一份存档')")
            page.reload()
            open_saved_games(page)
            page.locator('.title-save-list').get_by_text('第二份存档').wait_for()
            assert page.locator('.title-save-list').get_by_text('第一份存档').count()==0
            assert page.locator('.title-save-list li').filter(has_text='自动存档').count()==1
            assert not errors,errors
            print('PASS: 两个 IndexedDB 独立手动存档、刷新、读取并恢复阶段、删除隔离及自动存档')
            browser.close()
    finally:
        server.shutdown();t.join()
if __name__=='__main__':main()
