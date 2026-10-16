"""P3-02: actual Chromium module execution of 3/4-player complete games (UI flows belong to #32)."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        route=path.split('?',1)[0]
        if not route.startswith('/ReactMono/'):
            return str(ROOT/'dist'/'not-found')
        return str(ROOT/'dist'/route.removeprefix('/ReactMono/'))
    def log_message(self,*args): pass

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            launch={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
            if os.environ.get('CHROMIUM_PATH'): launch['executable_path']=os.environ['CHROMIUM_PATH']
            else: launch['channel']='chrome'
            browser=p.chromium.launch(**launch)
            page=browser.new_page(viewport={'width':1280,'height':800})
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/',wait_until='load')
            results=page.evaluate("""async()=>{
              const game=await import('./core/game.js');
              const sim=await import('./core/simulator.js');
              const results=[];
              for(const n of [3,4]){
                const config={...game.DEFAULT_CONFIG,maxRounds:12,
                  players:Array.from({length:n},(_,i)=>({id:'p'+(i+1),
                    name:'玩家'+(i+1),kind:i%2?'computer':'human'}))};
                let finished=0;
                for(let seed=0;seed<20;seed++){
                  const r=sim.runSimulation(seed,{config,maxActions:3000});
                  if(r.finalState.status!=='finished'||r.rejections!==0)throw Error('未完成 n='+n+' seed='+seed);
                  if(r.finalState.players.length!==n)throw Error('玩家丢失');
                  finished++;
                }
                results.push({players:n,completed:finished});
              }
              return results;
            }""")
            assert results==[{'players':3,'completed':20},{'players':4,'completed':20}],results
            assert not errors,errors
            print('PASS: 真实 Chromium /ReactMono/ 加载核心模块并执行多人整局',results)
            browser.close()
    finally:
        server.shutdown()
        thread.join()

if __name__=='__main__': main()
