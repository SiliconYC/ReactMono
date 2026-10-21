import type { Tile } from '../../core/types.js';
import type { Instance } from './Instances.js';

export type TownPart = Instance & Readonly<{shape:'box'|'roof'|'leaf';color:string}>;
export const TOWN = {wall:'#f4e5c9',stone:'#c9c5ab',trim:'#fff3da',glass:'#416b68',timber:'#79674e',roof:'#bf6653',greenRoof:'#517f76',hedge:'#789768'} as const;

/** Local parts stay inside the existing lot; ownership never changes the wall material. */
export function residentialParts(tile:Tile,owner:string|null,seat:number):TownPart[]{
  const parts:TownPart[]=[];
  const add=(x:number,y:number,z:number,sx:number,sy:number,sz:number,color:string,shape:TownPart['shape']='box')=>parts.push({x,y,z,sx,sy,sz,color,shape,tileId:tile.id});
  const level=tile.ownerId===null?0:tile.level??0;
  const roof=seat%2===0?TOWN.roof:TOWN.greenRoof;
  add(0,.035,0,1.5,.07,1.5,TOWN.stone);
  add(0,.078,0,1.38,.016,1.38,level===0?'#b6c694':'#d9d2b7');
  for(const x of [-.67,.67]) {
    add(x,.18,0,.07,.25,1.35,TOWN.trim);
    for(const z of [-.64,0,.64])add(x,.24,z,.1,.35,.1,TOWN.stone);
  }
  add(0,.16,-.66,1.34,.17,.07,TOWN.trim);
  add(0,.12,.69,1.5,.07,.08,owner??'#a0af7a');
  for(const x of [-.44,.44]) {
    add(x,.12,.57,.3,.1,.24,'#bda17d');
    add(x,.23,.57,.32,.17,.22,TOWN.hedge,'leaf');
  }
  if(level===0) {
    for(const x of [-.33,0,.33])add(x,.091,.17,.25,.02,.58,owner?'#d8ccb0':'#a3b985');
    for(const z of [-.4,-.2])add(0,.1,z,.8,.025,.08,'#9eaf7d');
  } else {
    const height=level===2?1.48:.81;
    add(0,.12+height/2,-.13,1.02,height,.88,TOWN.wall);
    add(0,.18,-.13,1.08,.15,.94,'#b7ae94');
    add(0,height+.16,-.13,1.18,.1,1.04,TOWN.trim);
    add(0,height+.4,-.13,1.24,.4,1.1,roof,'roof');
    add(0,height+.61,-.13,.07,.055,1.12,'#d5a27a');
    add(.32,height+.49,-.38,.14,.43,.17,'#c4b799');
    add(.32,height+.72,-.38,.2,.06,.22,TOWN.trim);
    add(0,.36,.323,.23,.48,.04,TOWN.timber);
    add(0,.43,.349,.13,.22,.018,TOWN.glass);
    add(.075,.3,.355,.025,.025,.022,'#e4ba6e');
    add(0,.11,.48,.43,.07,.27,TOWN.stone);
    add(0,.16,.37,.33,.04,.2,TOWN.trim);
    const window=(x:number,y:number,z:number)=>{
      const facing=z<0?-1:1;
      add(x,y,z,.26,.32,.04,TOWN.trim);
      add(x,y,z+facing*.027,.19,.24,.025,TOWN.glass);
      add(x,y,z+facing*.045,.025,.25,.025,TOWN.trim);
      add(x,y-.19,z,.33,.055,.12,TOWN.trim);
    };
    for(const x of [-.33,.33])window(x,.65,.331);
    for(const side of [-1,1]) {
      add(side*.522,.6,-.18,.035,.34,.33,TOWN.trim);
      add(side*.545,.6,-.18,.025,.25,.25,TOWN.glass);
    }
    window(0,.61,-.587);
    add(0,.76,.46,.52,.07,.34,roof);
    for(const x of [-.23,.23])add(x,.43,.57,.045,.62,.045,TOWN.trim);
    if(level===2) {
      add(0,1.03,-.13,1.07,.065,.92,owner??TOWN.trim);
      for(const x of [-.31,.31])window(x,1.35,.331);
      add(0,1.1,.48,.83,.075,.38,TOWN.stone);
      add(0,1.3,.65,.84,.045,.045,TOWN.trim);
      for(const x of [-.39,-.2,0,.2,.39])add(x,1.21,.65,.035,.2,.035,TOWN.trim);
      add(0,1.86,.21,.39,.38,.34,TOWN.wall);
      add(0,2.08,.21,.5,.18,.45,roof,'roof');
      add(0,1.88,.392,.18,.2,.03,TOWN.trim);
      add(0,1.88,.413,.12,.14,.02,TOWN.glass);
    }
  }
  if(owner) {
    add(-.56,.4,.67,.035,.64,.035,TOWN.timber);
    add(-.56,.66,.67,.23,.19,.055,owner);
    // One to four raised pips make ownership readable independently of hue.
    for(let i=0;i<=seat;i++)add(-.635+i*.05,.66,.704,.025,.055,.018,TOWN.trim);
  }
  if(tile.mortgaged) {
    if(level>0){
      const roofY=(level===2?1.48:.81)+.65;
      add(.16,roofY,-.13,.26,.04,.29,'#b56854');
      add(.16,roofY+.024,-.13,.17,.015,.035,TOWN.trim);
      add(.16,roofY+.024,-.13,.035,.016,.19,TOWN.trim);
    }
    add(.43,.38,.67,.04,.5,.04,TOWN.timber);
    add(.43,.58,.67,.33,.23,.06,'#b56854');
    add(.43,.58,.708,.2,.035,.02,TOWN.trim);
    add(.43,.58,.708,.035,.13,.023,TOWN.trim);
  }
  return parts;
}

export const GABLE_ROOF_VERTICES:readonly number[] = [
  -.5,-.5,-.5, 0,.5,-.5, .5,-.5,-.5,
  -.5,-.5,.5, .5,-.5,.5, 0,.5,.5,
  -.5,-.5,-.5, 0,.5,.5, 0,.5,-.5,
  -.5,-.5,-.5, -.5,-.5,.5, 0,.5,.5,
  .5,-.5,-.5, 0,.5,.5, .5,-.5,.5,
  .5,-.5,-.5, 0,.5,-.5, 0,.5,.5,
  -.5,-.5,-.5, .5,-.5,.5, -.5,-.5,.5,
  -.5,-.5,-.5, .5,-.5,-.5, .5,-.5,.5
];
