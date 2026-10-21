#!/usr/bin/env python3
"""Reproducible independent experiments for ReactMono Issue #121."""
import json, os, pathlib, subprocess, tempfile, shutil, time, hashlib, datetime, re, threading, http.server, socket
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/"docs/research/verification-issue-121/evidence"
OUT.mkdir(parents=True,exist_ok=True)
REPOS={
 "richman3d":("Yakamozli/richman-3d","32e7f01f9888a28b8fd1267f5488c455e15abe4a"),
 "richlife":("zawsstt/monopoly-rich-life","307c1761b150a7179fb0353618a95bc6effe3fee"),
 "rich4re":("tytannial/rich4-re","b7b76570f445ad07c0788314062b8500e77259e7")}
report={"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"os":os.uname().release,
        "reactmono_base_sha":"4494a16d017b0697fa7e74f9d450154e0c228ede",
        "pins":{k:v[1] for k,v in REPOS.items()},"commands":[],"views":[],
        "caveats":["Headless Chromium software rendering; simulated viewport is not a physical phone",
                   "Executable tests of a reconstruction do not prove original Richman 4 parity"]}
log=[]
def run(label,args,cwd=ROOT,timeout=240):
 print("RUN",label,flush=True)
 started=time.time()
 try:
  p=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)
  d={"label":label,"args":args,"cwd":str(cwd),"exit":p.returncode,"seconds":round(time.time()-started,1)}
  log.append("$ "+" ".join(map(str,args))+"\n"+p.stdout[-50000:])
 except Exception as e:
  d={"label":label,"args":args,"cwd":str(cwd),"exit":None,"error":str(e)}
  log.append(label+": "+str(e))
 report["commands"].append(d)
 print("END",label,d["exit"],flush=True)
 return d
def checkout(name,wd):
 repo,sha=REPOS[name];dst=wd/name
 args=["git","clone","--depth","1","https://github.com/"+repo+".git",str(dst)]
 if name=="richlife": args=["git","clone","--depth","1","--filter=blob:none","--sparse","https://github.com/"+repo+".git",str(dst)]
 if run("clone "+name,args,timeout=300)["exit"]!=0:return None
 if name=="richlife":
  if run("sparse assets",["git","sparse-checkout","set","css","js","src","assets/models","assets/img"],dst,180)["exit"]!=0:return None
 if run("pin "+name,["git","checkout","--detach",sha],dst,180)["exit"]!=0:return None
 head=subprocess.run(["git","rev-parse","HEAD"],cwd=dst,capture_output=True,text=True).stdout.strip()
 if head!=sha:raise RuntimeError(name+" SHA mismatch "+head)
 return dst
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*x):pass
def serve(directory,port):
 from functools import partial
 srv=http.server.ThreadingHTTPServer(("127.0.0.1",port),partial(Handler,directory=str(directory)))
 threading.Thread(target=srv.serve_forever,daemon=True).start()
 return srv
def browser(projs):
 try:
  from playwright.sync_api import sync_playwright
 except Exception as e:report["browser_error"]=str(e);return
 servers=[]
 if projs.get("richman3d"):servers.append(serve(projs["richman3d"],8121))
 if projs.get("richlife"):servers.append(serve(projs["richlife"],8122))
 with sync_playwright() as pw:
  opts={"headless":True,"args":["--no-sandbox","--disable-dev-shm-usage","--enable-webgl","--use-angle=swiftshader","--enable-unsafe-swiftshader"]}
  try:b=pw.chromium.launch(channel="chrome",**opts)
  except Exception:b=pw.chromium.launch(**opts)
  report["chromium_version"]=b.version
  for name,url in [("richman3d","http://127.0.0.1:8121/"),("richlife","http://127.0.0.1:8122/?auto=1&nofly=1&cdn=0"),("reactmono","http://127.0.0.1:4173/")]:
   for kind,w,h in [("desktop",1440,900),("mobile",390,844)]:
    d={"name":name,"viewport":kind,"size":[w,h],"url":url}
    if name!="reactmono" and not projs.get(name):d["blocked"]="clone failed";report["views"].append(d);continue
    page=b.new_page(viewport={"width":w,"height":h},device_scale_factor=1,has_touch=kind=="mobile")
    errors=[];page.on("pageerror",lambda e:errors.append(str(e)[:240]))
    try:
     response=page.goto(url,wait_until="domcontentloaded",timeout=30000)
     d["http"]=response.status if response else None
     page.wait_for_timeout(2600)
     if name=="richman3d":
      for btn in page.locator("#setup button").all():
       if btn.is_visible() and re.search("开始|开局|进入|Start",btn.inner_text(),re.I):
        btn.click(timeout=3000);d["clicked"]="setup start";break
     elif name=="richlife":
      if page.locator("#game-screen").count() and not page.locator("#game-screen").is_visible() and page.locator("#btn-start").is_visible():
       page.locator("#btn-start").click(timeout=3000);d["clicked"]="start"
     else:
      if page.get_by_role("button",name="开始游戏").count():
       page.get_by_role("button",name="开始游戏").first.click(timeout=4000)
       page.wait_for_timeout(400)
       if page.get_by_role("button",name="开始游戏",exact=True).count():
        page.get_by_role("button",name="开始游戏",exact=True).click(timeout=4000)
       d["clicked"]="start game"
     page.wait_for_timeout(4500)
     d["scene"]=page.evaluate("""() => {
      const cc=[...document.querySelectorAll('canvas')];
      const webgl=cc.filter(c=>{try{return !!(c.getContext('webgl2')||c.getContext('webgl'))}catch(e){return false}});
      return {canvas:cc.map(c=>({width:c.width,height:c.height,clientWidth:c.clientWidth})),
              webgl: webgl.length, body: document.body.innerText.slice(0,280),
              controls:[...document.querySelectorAll('button')].filter(b=>b.getBoundingClientRect().width>0).slice(0,12).map(b=>b.innerText.trim().slice(0,30))}}
     """)
     d["raf_ms"]=page.evaluate("""async()=>await Promise.race([
       (async()=>{let a=[],old=performance.now();for(let i=0;i<15;i++){
         await new Promise(requestAnimationFrame);let now=performance.now();if(i>2)a.push(now-old);old=now;
       } a.sort((x,y)=>x-y);return {n:a.length,median:a[Math.floor(a.length*.5)],p95:a[Math.floor(a.length*.95)]};})(),
       new Promise(resolve=>setTimeout(()=>resolve({timeout:true,n:0}),6000))])""")
     filename=name+"-"+kind+".png";path=OUT/filename
     page.screenshot(path=str(path),full_page=False,animations="disabled")
     d["screenshot"]=filename;d["sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
     d["render_confirmed"]=d["scene"]["webgl"]>0 and any(c["width"]>100 for c in d["scene"]["canvas"])
    except Exception as e:
     d["error"]=str(e)
     try:page.screenshot(path=str(OUT/(name+"-"+kind+"-failed.png")))
     except Exception:pass
    d["page_errors"]=errors[:15];report["views"].append(d)
    print("VIEW",name,kind,"render",d.get("render_confirmed"),"error",d.get("error"),flush=True)
    page.close()
  b.close()
 for s in servers:s.shutdown()
def economy(path):
 if not path:return
 # Extra independent cases, compiled with upstream's actual production rules.
 (path/"tests/unit/test_issue121.cpp").write_text(r'''
#include "microtest.h"
#include <cstring>
#include "game/app/turn_system.h"
#include "game/app/trade_market.h"
#include "game/game_state.h"
static rich4::Estate mk(const char* n,int o,int l,int t){
 rich4::Estate e{};strncpy(e.name,n,sizeof(e.name)-1);
 e.owner=o;e.level=l;e.type=t;
 for(int i=0;i<6;i++)e.fees[i]=100*(1<<i);
 return e;
}
MT_TEST(issue121_rent_owner_and_multiplier){
 rich4::GameState s;s.moneyMul=2;s.estates.push_back(rich4::Estate{});
 s.estates.push_back(mk("A",1,1,0));s.estates.push_back(mk("A",1,2,0));
 s.estates.push_back(mk("A",2,4,0));
 MT_EQ(rich4::estateRouteRent(s,1,s.estates[1]),1200);
}
MT_TEST(issue121_chain_multiplier){
 rich4::GameState s;s.moneyMul=3;s.estates.push_back(rich4::Estate{});
 s.estates.push_back(mk("A",1,1,1));s.estates.push_back(mk("B",1,2,1));
 s.estates.push_back(mk("C",2,1,1));
 MT_EQ(rich4::estateRouteRent(s,1,s.estates[1]),12000);
}
MT_TEST(issue121_same_trade_overwrite){
 rich4::GameState s;s.playerCount=2;
 rich4::queueTradeOrder(s,0,3,1,250,1);
 rich4::queueTradeOrder(s,0,3,1,400,1);
 MT_EQ(s.tradeSlots[0][0].price,400);
 MT_EQ(static_cast<int>(s.tradeSlots[0][1].type),0);
}
MT_TEST(issue121_trade_capacity_reuse){
 rich4::GameState s;s.playerCount=2;
 for(int i=1;i<=8;i++)rich4::queueTradeOrder(s,0,3,i,100+i,1);
 for(int i=0;i<7;i++) MT_EQ(static_cast<int>(s.tradeSlots[0][i].objId),i+1);
 rich4::removeTradeOrder(s,0,0);
 rich4::queueTradeOrder(s,0,3,8,108,1);
 MT_EQ(static_cast<int>(s.tradeSlots[0][6].objId),8);
}
''',encoding="utf-8")
 build=path/"build-issue121"
 if run("cmake configure",["cmake","-S",str(path),"-B",str(build),"-DCMAKE_BUILD_TYPE=Release"],timeout=360)["exit"]==0:
  if run("cmake build unit",["cmake","--build",str(build),"--target","rich4_tests","-j","3"],timeout=1100)["exit"]==0:
   run("ctest rent/trade",["ctest","--test-dir",str(build),"--output-on-failure"],timeout=150)
def main():
 work=pathlib.Path(tempfile.mkdtemp(prefix="reactmono-121-"))
 projs={};proc=None
 try:
  for name in REPOS:projs[name]=checkout(name,work)
  if projs.get("richman3d"):run("richman3d smoke",["node","test/smoke.mjs","2"],projs["richman3d"],120)
  economy(projs.get("rich4re"))
  run("CJK font setup",["bash","-lc","if ! fc-list :lang=zh family | grep -q .; then sudo apt-get update -qq && sudo apt-get install -y -qq --no-install-recommends fonts-wqy-microhei; fi"],timeout=240)
  if run("ReactMono npm ci",["npm","ci","--ignore-scripts"],timeout=360)["exit"]==0:
   proc=subprocess.Popen(["npm","run","main:dev","--","--host","127.0.0.1","--port","4173","--strictPort"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   time.sleep(7)
  browser(projs)
 finally:
  if proc:proc.terminate()
  shutil.rmtree(work,ignore_errors=True)
  (OUT/"run.log").write_text("\n\n".join(log),encoding="utf-8")
  (OUT/"run.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  print("EVIDENCE_SAVED",len(report["views"]),len(report["commands"]),flush=True)
if __name__=="__main__":main()
