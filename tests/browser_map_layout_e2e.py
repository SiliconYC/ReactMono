"""P3 map grid on mobile and desktop: all cells accessible, no overlap."""
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler, open_new_game_setup, select_map

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    t=Thread(target=server.serve_forever,daemon=True);t.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox'])
            for width in [390,1440]:
                page=browser.new_page(viewport={'width':width,'height':900})
                page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
                open_new_game_setup(page)
                report=page.evaluate("""async()=>{
                  const maps=await import('./core/maps.js');
                  const check=board=>{
                    const rect=[...board.querySelectorAll('.tile')].map(t=>t.getBoundingClientRect());
                    const overlap=rect.some((a,i)=>rect.some((b,j)=>i!==j&&
                        Math.max(a.left,b.left)<Math.min(a.right,b.right)-1&&
                        Math.max(a.top,b.top)<Math.min(a.bottom,b.bottom)-1));
                    return {cells:rect.length,overlap,positive:rect.every(r=>r.width>2&&r.height>2)};
                  };
                  const original=check(document.querySelector('.board'));
                  const map=maps.INTERNAL_TEST_MAP;
                  const scratch=document.createElement('div');
                  scratch.className='board';
                  scratch.style.gridTemplateColumns='repeat('+map.columns+',minmax(0,1fr))';
                  scratch.style.gridTemplateRows='repeat('+map.rows+',minmax(0,1fr))';
                  scratch.style.width=document.querySelector('.board').getBoundingClientRect().width+'px';
                  for(let i=0;i<map.cells.length;i++){
                    const el=document.createElement('div');el.className='tile';
                    el.style.gridColumn=map.cells[i].column;
                    el.style.gridRow=map.cells[i].row;
                    scratch.appendChild(el);
                  }
                  document.querySelector('.board-card').appendChild(scratch);
                  const internal=check(scratch);scratch.remove();
                  return {original,internal};
                }""")
                assert report['original']['cells']==24 and not report['original']['overlap'] and report['original']['positive'],report
                assert report['internal']['cells']==16 and not report['internal']['overlap'] and report['internal']['positive'],report
                print('PASS: dynamic board grid',width,report)
                page.close()
            browser.close()
    finally:
        server.shutdown();t.join()
if __name__=='__main__':main()
