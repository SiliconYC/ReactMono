import type {GameEvent} from '../core/game.js';
export type SoundKind='dice'|'step'|'gain'|'pay'|'card'|'facility'|'finish';
export function classifySound(events:readonly GameEvent[]):SoundKind|null{
 const has=(...names:string[])=>events.some(e=>names.includes(e.type));
 if(has('game_finished','player_bankrupt'))return 'finish';
 if(has('facility_entered','detention_skipped'))return 'facility';
 if(has('card_received','card_used','shop_purchased'))return 'card';
 if(has('rent_paid','property_bought','property_upgraded','bank_deposited','loan_repaid','event_fee','stock_bought'))return 'pay';
 if(has('event_bonus','property_sold','bank_withdrawn','bank_interest','loan_borrowed','stock_sold'))return 'gain';
 if(has('die_rolled'))return 'dice';
 if(has('player_moved'))return 'step';
 return null;
}
/** All sound comes from tiny locally synthesized Web Audio oscillators; no copyrighted samples. */
export class SoundController{
 private ctx:AudioContext|null=null;
 private lastAt=0;
 private enabled=false;
 private volume=.3;
 constructor(){
  try{this.enabled=localStorage.getItem('reactmono-audio-enabled')==='1';
      this.volume=Math.min(1,Math.max(0,Number(localStorage.getItem('reactmono-audio-volume')??'.3')||.3));}catch{}
 }
 get isEnabled(){return this.enabled;}
 get level(){return this.volume;}
 setVolume(value:number):void{
  this.volume=Math.min(1,Math.max(0,value));
  try{localStorage.setItem('reactmono-audio-volume',String(this.volume));}catch{}
 }
 async setEnabled(value:boolean):Promise<void>{
  this.enabled=value;
  try{localStorage.setItem('reactmono-audio-enabled',value?'1':'0');}catch{}
  if(!value){try{await this.ctx?.suspend();}catch{}return;}
  await this.activate();
 }
 async activate():Promise<void>{
  if(!this.enabled||typeof window==='undefined'||!('AudioContext' in window))return;
  try{
   if(!this.ctx)this.ctx=new AudioContext({latencyHint:'interactive'});
   if(this.ctx.state==='suspended')await this.ctx.resume();
  }catch{/* Unsupported or policy-blocked audio must never block a turn. */}
 }
 play(events:readonly GameEvent[]):void{
  if(!this.enabled||this.volume<=0||!this.ctx||this.ctx.state!=='running'||document.hidden)return;
  const kind=classifySound(events);if(!kind)return;
  const now=performance.now();if(now-this.lastAt<65)return;
  this.lastAt=now;
  const patterns:Record<SoundKind,readonly [number,number,number][]> = {
   dice:[[350,0,.075],[465,.082,.075],[510,.165,.075]],
   step:[[350,0,.045]],
   gain:[[530,0,.085],[670,.10,.13]],
   pay:[[400,0,.085],[320,.095,.14]],
   card:[[620,0,.07],[790,.08,.10],[940,.17,.10]],
   facility:[[440,0,.12],[360,.14,.2]],
   finish:[[520,0,.12],[660,.14,.12],[810,.28,.24]]
  };
  try{
   const start=this.ctx.currentTime+.01;
   for(const [frequency,offset,duration] of patterns[kind]){
    const osc=this.ctx.createOscillator(), gain=this.ctx.createGain();
    osc.type=kind==='dice'||kind==='step'?'triangle':'sine';
    osc.frequency.setValueAtTime(frequency,start+offset);
    gain.gain.setValueAtTime(0,start+offset);
    gain.gain.linearRampToValueAtTime(this.volume*.045,start+offset+.012);
    gain.gain.exponentialRampToValueAtTime(.0001,start+offset+duration);
    osc.connect(gain);gain.connect(this.ctx.destination);
    osc.start(start+offset);osc.stop(start+offset+duration+.015);
    osc.onended=()=>{osc.disconnect();gain.disconnect();};
   }
  }catch{/* Sound is optional: never change rules on an audio failure. */}
 }
 dispose():void{if(this.ctx){void this.ctx.close().catch(()=>{});this.ctx=null;}}
}
