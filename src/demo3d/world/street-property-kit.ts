import type { Tile } from '../../core/types.js';
import { UrbanModel, type UrbanPart } from './urban-kit.js';

const families=[
  {wall:'#e5c49d',roof:'#b9765e',gable:true},
  {wall:'#c5d0ba',roof:'#638c83',gable:false},
  {wall:'#d6b29d',roof:'#8c979c',gable:true},
  {wall:'#e4d4b5',roof:'#74918c',gable:false},
  {wall:'#b5c5c5',roof:'#bd795e',gable:true},
  {wall:'#d8c5a2',roof:'#6d8872',gable:true}
] as const;

/** Sales plots stay open; architectural families depend on the address, not owner hue. */
export function streetPropertyParts(tile:Tile,owner:string|null,seat:number):UrbanPart[] {
  const m=new UrbanModel(),style=families[tile.id%families.length],level=tile.ownerId===null?0:tile.level??0;
  m.box(0,level===0?.007:.025,0,1.48,level===0?.014:.05,1.4,level===0?'#aebb98':'#c6c4b4');
  m.box(0,.057,.57,1.46,.014,.24,owner??'#d5c49e');
  if(level===0) {
    if(tile.id%3===0) {
      m.box(-.25,.059,-.15,.7,.015,.72,'#a4b382');
      m.pot(.46,-.4,.7);
    } else if(tile.id%3===1) {
      m.box(-.2,.058,-.04,.6,.014,.64,'#c3b698');
      m.box(.42,.058,-.13,.31,.014,.8,'#9eaf84');
      m.add('leaf',.42,.18,-.39,.31,.24,.3,'#8ba474');
    } else {
      for(const z of [-.35,-.08,.19])m.box(-.12,.06,z,.96,.016,.12,'#d9d0b7');
      m.pot(-.5,-.49,.55,true);
    }
    for(const x of [-.29,.29])m.box(x,.27,-.48,.035,.46,.035,'#947858');
    m.sign(owner?'产权':'待售',0,.49,-.45,.63,.19);
  } else {
    const height=level===2?1.63:.88,w=tile.id%3===0?1.08:1.18,d=.88;
    m.body(w,d,height,style.wall);
    if(style.gable) {
      m.add('roof',0,height+.39,-.03,w+.24,.48,1.09,style.roof);
      m.box(-.35,height+.49,-.25,.12,.44,.15,'#d6c8ad');
      m.box(-.35,height+.74,-.25,.18,.06,.2,'#f2e9d4');
    } else {
      m.box(0,height+.28,0,w+.22,.09,1.06,style.roof);
      for(const x of [-1,1])m.box(x*(w/2+.04),height+.39,0,.07,.24,.98,'#e9dfc9');
      m.box(0,height+.39,-.48,w+.1,.24,.07,'#e9dfc9');
      m.box(.28,height+.4,-.18,.33,.17,.33,'#92a69a');
    }
    if(tile.id%2===0) {
      m.window(-.25,.55,.47,.34,.53,tile.id%3===0);
      m.window(.34,.46,.47,.25,.68,true);
    } else {
      m.window(-.32,.56,.47,.23,.47);
      m.window(.29,.56,.47,.29,.5);
      m.box(0,.34,.52,.2,.5,.055,'#7d705b');
      m.box(0,.4,.555,.12,.23,.025,'#486f77');
    }
    m.sideWindows(w,d,1);
    if(level===2) {
      m.box(0,1.02,0,w+.06,.07,d+.06,owner??'#e9dfc9');
      for(const x of [-.31,.31])m.window(x,1.37,.47,.29,.42,tile.id%3===2);
      for(const side of [-1,1])m.box(side*(w/2+.025),1.35,-.07,.035,.38,.29,'#486f77');
      if(tile.id%2)m.balcony(0,1.38,.49,.87);
      else {m.box(0,1.91,.27,.35,.26,.27,style.wall);m.add('roof',0,2.09,.27,.47,.18,.38,style.roof);m.window(0,1.94,.419,.12,.13);}
    }
    if(tile.id%3===1) {
      for(let i=0;i<6;i++)m.box(-.5+i*.2,.88,.62,.2,.06,.34,i%2?'#eee6ce':style.roof);
    } else {
      m.box(0,.83,.59,.49,.06,.29,style.roof);
      for(const x of [-.21,.21])m.box(x,.46,.66,.035,.68,.035,'#e9dfc9');
    }
    m.box(0,.092,.55,.54,.08,.28,'#ded8c5');
    if(tile.id%2===0)m.pot(-.56,.51,.6);
  }
  if(owner) {
    m.box(-.66,.28,.5,.035,.48,.035,'#7c715b');
    m.box(-.57,.51,.5,.25,.17,.035,owner);
    for(let i=0;i<=seat;i++)m.box(-.66+i*.052,.51,.525,.022,.055,.015,'#fff0d3');
  }
  if(tile.mortgaged) {
    m.box(.42,.42,.57,.38,.24,.06,'#b56854');m.box(.42,.42,.608,.24,.04,.02,'#fff0d3');
    m.box(.42,.42,.608,.04,.16,.02,'#fff0d3');
    if(level>0) {const y=(level===2?1.63:.88)+.68;m.box(.15,y,0,.3,.025,.3,'#b56854');m.box(.15,y+.019,0,.21,.014,.04,'#fff0d3');}
  }
  return m.parts.map(p=>({...p,tileId:tile.id}));
}
