import type { Instance } from './Instances.js';
import { URBAN_SCENERY_KINDS } from '../../core/level-world.js';

export type UrbanKind=typeof URBAN_SCENERY_KINDS[number];
export type UrbanShape='box'|'roof'|'arch'|'cylinder'|'cone'|'leaf'|'sphere'|'sign';
export type UrbanPart=Instance&Readonly<{shape:UrbanShape;sx:number;sy:number;sz:number;label?:string;alpha?:number}>;
export const URBAN_LABELS=['晴湾咖啡','海风旅店','花间书屋','暖麦面包','晴湾公寓','花房','晴湾市集','木作工坊','巴士站','待售','产权','晴湾花园'] as const;
const C={trim:'#f5edd9',stone:'#c5c3b4',glass:'#486f77',dark:'#3e5759',metal:'#536861',wood:'#947858',roof:'#bc6f55',green:'#627f65',paving:'#d3d2c5'};

/** Author-sized assets share primitive batches; no runtime scatter or game state. */
export class UrbanModel {
  readonly parts:UrbanPart[]=[];
  add(shape:UrbanShape,x:number,y:number,z:number,sx:number,sy:number,sz:number,color:string,extra:Partial<UrbanPart>={}):void {
    this.parts.push({shape,x,y,z,sx,sy,sz,color,...extra});
  }
  box(x:number,y:number,z:number,sx:number,sy:number,sz:number,color:string):void {this.add('box',x,y,z,sx,sy,sz,color);}
  sign(label:string,x:number,y:number,z:number,width:number,height=.25):void {
    this.box(x,y,z,width+.12,height+.09,.075,C.dark);
    this.add('sign',x,y,z+.044,width,height,.01,'#ffffff',{label});
  }
  window(x:number,y:number,z:number,width=.38,height=.52,arch=false):void {
    this.add(arch?'arch':'box',x,y,z,width+.1,height+.1,.09,C.trim);
    this.add(arch?'arch':'box',x,y,z+.055,width,height,.035,C.glass);
    this.box(x,y-.02,z+.08,.035,height-.04,.025,C.trim);
    this.box(x,y-.04,z+.08,width,.035,.025,C.trim);
    this.box(x,y-height/2-.075,z+.035,width+.18,.07,.18,C.trim);
  }
  sideWindows(width:number,depth:number,levels:number):void {
    for(const side of [-1,1])for(let floor=0;floor<levels;floor++)for(const z of [-depth*.25,depth*.25]) {
      this.box(side*(width/2+.024),.65+floor*.85,z,.06,.5,.39,C.trim);
      this.box(side*(width/2+.06),.65+floor*.85,z,.025,.39,.29,C.glass);
      this.box(side*(width/2+.065),.34+floor*.85,z,.13,.055,.5,C.trim);
    }
    for(let floor=0;floor<levels;floor++)for(const x of [-width*.26,width*.26]) {
      this.box(x,.65+floor*.85,-depth/2-.022,.4,.5,.06,C.trim);
      this.box(x,.65+floor*.85,-depth/2-.06,.3,.39,.025,C.glass);
    }
  }
  body(width:number,depth:number,height:number,color:string):void {
    this.box(0,.055,0,width+.18,.11,depth+.18,C.stone);
    this.box(0,height/2+.1,0,width,height,depth,color);
    this.box(0,.22,0,width+.08,.18,depth+.08,'#b6afa0');
    this.box(0,height+.12,0,width+.17,.12,depth+.17,C.trim);
    this.box(0,height+.22,0,width+.24,.07,depth+.24,color);
  }
  flatRoof(width:number,depth:number,y:number,color:string):void {
    this.box(0,y,0,width,.08,depth,'#a2b7b5');
    for(const x of [-1,1])this.box(x*width/2,y+.13,0,.09,.28,depth+.08,color);
    for(const z of [-1,1])this.box(0,y+.13,z*depth/2,width,.28,.09,color);
    this.box(width*.2,y+.18,-depth*.2,.46,.3,.48,'#82908c');
    for(const x of [-.13,0,.13])this.box(width*.2+x,y+.35,-depth*.2,.045,.03,.35,C.dark);
  }
  awning(x:number,y:number,z:number,width:number,color:string):void {
    const count=Math.ceil(width/.2);
    for(let i=0;i<count;i++) {
      const xx=x-width/2+(i+.5)*width/count,c=i%2?C.trim:color;
      this.add('box',xx,y,z,width/count,.065,.65,c,{rx:.2});
      this.box(xx,y-.12,z+.31,width/count,.18,.05,c);
    }
    for(const side of [-1,1])this.box(x+side*(width/2-.04),y-.29,z+.22,.035,.5,.035,C.metal);
  }
  balcony(x:number,y:number,z:number,width:number):void {
    this.box(x,y-.34,z+.13,width+.16,.075,.37,C.stone);
    this.box(x,y-.01,z+.31,width+.14,.045,.035,C.dark);
    for(let i=0;i<6;i++)this.box(x-width/2+i*width/5,y-.17,z+.31,.025,.3,.025,C.dark);
  }
  pot(x:number,z:number,scale=1,flowers=false):void {
    this.add('cylinder',x,.15*scale,z,.32*scale,.3*scale,.32*scale,'#b98368');
    this.add('leaf',x,.39*scale,z,.46*scale,.35*scale,.46*scale,flowers?'#c68f92':'#789a6c');
  }
}

function building(m:UrbanModel,kind:UrbanKind,color:string):boolean {
  switch(kind) {
    case 'corner-cafe': {
      const w=2.8,d=2.15,h=3.05;m.body(w,d,h,color);m.flatRoof(w,d,h+.3,color);
      for(const x of [-.88,0,.88]) {
        m.window(x,.67,d/2+.02,.5,.91,true);
        for(const y of [1.7,2.57])m.window(x,y,d/2+.02,.42,.58,true);
      }
      for(const y of [1.22,2.14])m.box(0,y,0,w+.1,.08,d+.1,C.trim);
      m.awning(0,1.3,1.37,2.95,'#667f78');m.sign('晴湾咖啡',0,1.59,1.14,1.18);
      m.sideWindows(w,d,3);m.pot(-1.26,1.5,.65);m.pot(1.26,1.5,.65);
      m.box(-.8,3.58,-.55,.18,.52,.18,C.stone);break;
    }
    case 'hotel': {
      const w=2.35,d=2.1,h=4.15;m.body(w,d,h,color);m.flatRoof(w,d,h+.3,C.trim);
      m.window(0,.65,1.09,.65,1,true);
      for(const y of [1.6,2.48,3.36])for(const x of [-.68,0,.68]) {m.window(x,y,1.09,.35,.58,true);if(y>2)m.balcony(x,y,1.16,.42);}
      m.awning(0,1.2,1.33,1.4,'#d6b965');m.sign('海风旅店',0,3.98,1.18,1.5,.3);
      m.sideWindows(w,d,4);m.box(1.3,2.5,.72,.32,2.1,.17,C.dark);
      for(const y of [1.82,2.25,2.68,3.11])m.box(1.31,y,.82,.16,.2,.035,'#e4bc72');
      m.add('cylinder',-.6,4.85,-.4,.62,.73,.62,C.stone);m.add('cone',-.6,5.31,-.4,.78,.22,.78,'#96aaa9');break;
    }
    case 'bookshop': {
      const w=2.15,d=1.8,h=2.65;m.body(w,d,h,color);m.flatRoof(w,d,h+.3,color);
      for(const x of [-.57,.57])for(const y of [1.55,2.26])m.window(x,y,.93,.43,.52);
      m.window(-.48,.64,.94,.82,.79);m.window(.61,.63,.94,.47,.92,true);
      for(let i=0;i<8;i++)m.box(-.82+i*.09,.5,1,.055,.22+(i%3)*.05,.05,['#c28068','#dab76c','#7a9795'][i%3]);
      m.sign('花间书屋',0,1.17,1.01,1.6);m.sideWindows(w,d,3);m.pot(-.95,1.2,.7);break;
    }
    case 'bakery': {
      const w=2.7,d=1.9,h=1.45;m.body(w,d,h,color);
      m.add('roof',0,h+.54,0,w+.4,.67,d+.32,C.roof);
      m.box(.82,2.16,-.3,.22,.8,.22,C.stone);m.box(.82,2.59,-.3,.3,.08,.3,C.trim);
      m.window(-.51,.65,.99,1.08,.75,true);m.window(.86,.61,.99,.5,.88);
      m.awning(0,1.27,1.28,2.72,'#b56f56');m.sign('暖麦面包',0,1.83,1.08,1.22);
      m.sideWindows(w,d,1);for(const x of [-.85,-.5,-.15])m.add('sphere',x,.51,1.04,.22,.12,.11,'#d9aa69');break;
    }
    case 'apartment': {
      const w=3.1,d=2.1,h=3.63;m.body(w,d,h,color);m.flatRoof(w,d,h+.3,C.trim);
      for(const y of [.72,1.6,2.48,3.28])for(const x of [-1,0,1]){m.window(x,y,1.08,.44,.58);if(y>1)m.balcony(x,y,1.17,.68);}
      m.sideWindows(w,d,4);m.sign('晴湾公寓',0,.98,1.13,1.18,.22);
      m.box(-.8,4.18,-.3,.85,.22,.62,'#96aaa3');
      for(const x of [-1.3,1.3])m.box(x,4.35,.55,.055,.8,.055,C.wood);
      m.box(0,4.74,.55,2.65,.035,.035,C.dark);
      for(const x of [-.9,-.4,.25,.85])m.box(x,4.57,.55,.32,.33,.025,x>0?'#d6ba83':'#809c9e');break;
    }
    case 'greenhouse': {
      const w=2.85,d=1.9;m.body(w,d,1.28,'#a7c8b5');
      m.add('roof',0,1.68,0,3.05,.75,2.1,'#91b9ad');
      for(const x of [-1.38,-.9,-.45,0,.45,.9,1.38])m.box(x,.7,.99,.055,1.28,.05,C.trim);
      for(const z of [-1,-.5,0,.5,1])for(const side of [-1,1])m.add('box',side*.76,1.68,z,1.7,.05,.055,C.trim,{rz:-side*.46});
      m.box(0,.84,1.02,2.8,.055,.055,C.trim);
      m.window(0,.6,1.04,.5,.9);m.sign('花房',0,1.24,1.09,.7,.2);
      for(const x of [-1.3,-.7,.7,1.3])m.pot(x,1.29,.8,x<0);break;
    }
    case 'market-hall': {
      const w=4.2,d=2.25;m.body(w,d,1.75,color);m.add('roof',0,2.29,0,4.55,.86,2.6,'#618b86');
      for(const x of [-1.48,-.5,.5,1.48])m.window(x,.85,1.16,.7,1.13,true);
      for(const x of [-2,-1,0,1,2])m.box(x,1,1.22,.12,1.85,.14,C.trim);
      m.box(0,2.76,0,1.2,.2,.65,C.trim);m.sign('晴湾市集',0,2.1,1.33,1.7,.3);
      m.sideWindows(w,d,2);
      const rear=new UrbanModel();
      for(const x of [-1.48,-.5,.5,1.48])rear.window(x,.85,1.17,.7,1.13,true);
      rear.sign('晴湾市集',0,1.77,1.29,1.65,.27);
      rear.awning(0,1.56,1.42,3.65,'#d5b66f');
      m.parts.push(...rear.parts.map(p=>({...p,x:-p.x,z:-p.z,rotation:Math.PI})));break;
    }
    case 'workshop': {
      const w=2.7,d=2;m.body(w,d,1.7,color);m.add('roof',0,2.12,0,3.02,.67,2.3,'#778d8d');
      m.box(-.65,.75,1.03,.95,1.22,.07,'#8a7460');
      for(const y of [.29,.49,.69,.89,1.09,1.29])m.box(-.65,y,1.08,.85,.035,.025,C.wood);
      m.window(.73,.86,1.03,.66,.63);m.sign('木作工坊',0,1.63,1.12,1.5,.25);
      m.box(.87,2.23,-.3,.4,.95,.45,C.stone);m.box(.87,2.75,-.3,.52,.1,.55,C.trim);
      m.sideWindows(w,d,1);for(let i=0;i<4;i++)m.box(1.2,.18+i*.09,1.4,.75,.08,.23,'#ba9b71');break;
    }
    default:return false;
  }
  return true;
}

function vehicle(m:UrbanModel,color:string,van:boolean):void {
  m.box(0,.23,0,.75,.28,1.65,color);m.box(0,.46,-.13,.64,.38,van?1.2:.9,color);
  m.box(0,.48,.34,.57,.24,.035,C.glass);m.box(0,.49,van?-.75:-.6,.57,.2,.035,C.glass);
  if(!van)for(const side of [-1,1])m.box(side*.328,.49,-.08,.025,.23,.69,C.glass);
  for(const side of [-1,1])for(const z of [-.53,.53]) {
    m.add('cylinder',side*.36,.18,z,.34,.12,.34,'#3f4947',{rz:Math.PI/2});
    m.add('cylinder',side*.428,.18,z,.17,.02,.17,'#a4aea7',{rz:Math.PI/2});
  }
  for(const side of [-1,1]){m.box(side*.23,.28,.843,.18,.12,.025,'#f2e1ad');m.box(side*.23,.28,-.843,.12,.13,.025,'#bd6a55');}
  m.box(0,.14,.84,.66,.06,.06,C.stone);m.box(0,.14,-.84,.66,.06,.06,C.stone);
}

export function urbanParts(kind:UrbanKind,color:string):UrbanPart[] {
  const m=new UrbanModel();if(building(m,kind,color))return m.parts;
  switch(kind) {
    case 'cypress':
      m.add('cylinder',0,.4,0,.16,.8,.16,C.wood);
      for(const [y,w,h]of [[.95,.65,1.55],[1.62,.5,1.5],[2.18,.31,1.05]])m.add('cone',0,y,0,w,h,w,color);break;
    case 'birch':
      m.add('cylinder',0,1.02,0,.16,2.04,.16,'#d5d1b9');
      for(const y of [.4,.75,1.15,1.6])m.box(0,y,.087,.15,.04,.015,'#8e9281');
      m.add('leaf',-.34,1.62,.08,.95,1.05,1,color);m.add('leaf',.3,2.05,-.12,1.1,1.25,1.05,color);m.add('leaf',-.08,2.63,0,.75,.85,.76,'#9bb17c');break;
    case 'willow':
      m.add('cylinder',0,.74,0,.28,1.48,.28,C.wood);
      m.add('leaf',0,1.7,0,2.3,1.1,1.9,color);
      for(const [x,z] of [[-.72,0],[.72,.08],[0,-.68],[-.3,.63],[.4,.6]])m.add('leaf',x,1.15,z,.7,1.1,.65,'#8da878');break;
    case 'jacaranda':
      m.add('cylinder',0,.85,0,.21,1.7,.21,C.wood);
      for(const [x,y,z]of [[-.58,1.9,0],[.48,2.1,-.15],[0,2.4,.32]])m.add('leaf',x,y,z,1.3,.95,1.18,color);break;
    case 'umbrella':
      m.add('cylinder',0,.72,0,.045,1.44,.045,C.wood);m.add('cylinder',0,.035,0,.4,.07,.4,C.stone);
      m.add('cone',0,1.57,0,1.65,.48,1.65,color);m.add('cone',0,1.59,0,.8,.5,.8,C.trim);break;
    case 'cafe-table':
      m.add('cylinder',0,.55,0,.64,.075,.64,C.trim);m.add('cylinder',0,.28,0,.055,.55,.055,C.metal);
      m.add('cylinder',0,.045,0,.38,.09,.38,C.metal);
      for(const side of [-1,1]) {
        m.box(side*.55,.3,0,.31,.06,.31,C.wood);m.box(side*.68,.49,0,.045,.4,.32,C.wood);
        for(const z of [-.12,.12])m.box(side*.55,.15,z,.035,.3,.035,C.metal);
      }break;
    case 'market-cart':
      m.box(0,.55,0,1.1,.6,.65,color);m.box(0,.89,0,1.22,.1,.8,C.wood);
      for(const x of [-.53,.53]){m.add('cylinder',x,.22,0,.4,.08,.4,C.dark,{rz:Math.PI/2});m.box(x,1.28,0,.045,.8,.045,C.wood);}
      for(let i=0;i<6;i++)m.box(-.5+i*.2,1.74,0,.2,.09,.95,i%2?C.trim:color);
      for(const x of [-.3,0,.3])m.add('sphere',x,1.02,.04,.19,.19,.19,'#dcad68');break;
    case 'bus-stop':
      for(const x of [-1.05,1.05])m.box(x,.86,-.18,.055,1.72,.055,C.metal);
      m.box(0,1.76,0,2.42,.1,.88,color);m.box(0,.85,-.29,2.13,1.6,.055,'#a8bfba');
      for(const x of [-.7,.7])m.box(x,.36,0,.055,.7,.055,C.metal);
      m.box(0,.43,0,1.7,.065,.34,C.wood);m.sign('巴士站',0,1.57,.48,.9,.18);break;
    case 'car':case 'van':vehicle(m,color,kind==='van');break;
    case 'fountain':
      m.add('cylinder',0,.1,0,2.7,.2,2.7,C.stone);m.add('cylinder',0,.22,0,2.42,.08,2.42,'#80b9b5');
      m.add('cylinder',0,.62,0,.27,.85,.27,C.trim);m.add('cylinder',0,.86,0,1.2,.12,1.2,C.trim);
      m.add('cylinder',0,.94,0,1.04,.055,1.04,'#91c3be');m.add('cylinder',0,1.18,0,.17,.49,.17,C.trim);
      m.add('cylinder',0,1.41,0,.64,.09,.64,C.trim);m.add('sphere',0,1.57,0,.22,.25,.22,'#a6d1cc');break;
    case 'hydrant':
      m.add('cylinder',0,.24,0,.19,.48,.19,color);m.add('sphere',0,.5,0,.25,.16,.25,color);
      m.box(0,.31,0,.39,.12,.12,color);m.add('cylinder',0,.035,0,.29,.07,.29,C.metal);break;
    case 'bicycle':
      for(const z of [-.4,.4]) {
        m.add('cylinder',0,.29,z,.55,.045,.55,C.dark,{rz:Math.PI/2});
        m.add('cylinder',.026,.29,z,.42,.048,.42,C.paving,{rz:Math.PI/2});
      }
      m.box(0,.48,0,.045,.055,.7,color);m.box(0,.39,0,.05,.28,.05,color);
      m.box(0,.63,-.16,.18,.06,.26,C.dark);m.box(0,.57,.38,.04,.6,.04,C.metal);m.box(0,.87,.38,.37,.045,.045,C.dark);break;
    case 'planter':
      m.box(0,.16,0,1.3,.32,.6,C.stone);m.box(0,.34,0,1.22,.05,.51,'#897860');
      for(const x of [-.4,0,.4])m.add('leaf',x,.55,0,.5,.5,.48,color);break;
    case 'bollard':
      m.add('cylinder',0,.29,0,.11,.58,.11,C.metal);m.add('sphere',0,.6,0,.15,.15,.15,C.metal);m.add('cylinder',0,.035,0,.22,.07,.22,C.stone);break;
    case 'street-lamp':
      m.add('cylinder',0,1.2,0,.08,2.4,.08,C.metal);m.add('cylinder',0,.07,0,.2,.14,.2,C.stone);
      m.box(.24,2.38,0,.54,.065,.065,C.metal);m.box(.5,2.32,0,.28,.11,.2,'#e6d6a2');break;
    case 'crosswalk':
      for(const x of [-.72,-.43,-.14,.15,.44,.73])m.box(x,.011,0,.18,.014,1.62,'#e6e3d5');break;
    case 'road-dash':m.box(0,.011,0,.75,.014,.055,'#d6cc9d');break;
    case 'kerb':m.box(0,.043,0,1.5,.078,.13,'#bdbfaf');m.box(0,.088,0,1.48,.012,.16,'#e5e0d0');break;
  }
  return m.parts;
}
