import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

/** 瓦垄直接进入几何，转动镜头和统一阴影下仍保留折面，而非依赖画出的细线。 */
export function foldedRoofGeometry():THREE.BufferGeometry {
  const profile=[[1.08,.075],[1.02,.025],[.91,.07],[.77,.135],[.61,.235],[.44,.355],[.29,.49],[.15,.615],[.065,.72]];
  const sectors=256,steps=3,positions:number[]=[],colors:number[]=[],indices:number[]=[];
  for(let row=0;row<=(profile.length-1)*steps;row++){
    const segment=Math.min(profile.length-2,Math.floor(row/steps)),t=(row-segment*steps)/steps;
    const radius=THREE.MathUtils.lerp(profile[segment][0],profile[segment+1][0],t),height=THREE.MathUtils.lerp(profile[segment][1],profile[segment+1][1],t);
    for(let i=0;i<=sectors;i++){
      const angle=i/sectors*Math.PI*2,ridge=(1+Math.cos(angle*64))/2;
      const r=radius+ridge*.012*radius;
      positions.push(Math.sin(angle)*r,height+ridge*.026*Math.min(1,radius*2),Math.cos(angle)*r);
      const c=new THREE.Color('#ffffff').multiplyScalar(.75+ridge*.23-(row%3===0?.065:0));colors.push(c.r,c.g,c.b);
      if(row<(profile.length-1)*steps&&i<sectors){
        const a=row*(sectors+1)+i,b=a+sectors+1;
        indices.push(a,a+1,b,a+1,b+1,b);
      }
    }
  }
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.setIndex(indices);g.computeVertexNormals();
  return g;
}

export function constructionPose(seconds:number,reducedMotion:boolean):{scaleY:number;dust:number;finished:boolean} {
  if(reducedMotion||seconds>=.82)return {scaleY:1,dust:0,finished:true};
  const t=Math.max(0,seconds)/.82,settle=t-1;
  const scaleY=t===0?.05:Math.max(.05,1+2.25*settle**3+1.25*settle**2);
  return {scaleY,dust:Math.sin(Math.min(1,t*1.5)*Math.PI)*(1-t),finished:false};
}

function gable(width:number,depth:number,height:number):THREE.BufferGeometry {
  const w=width/2,d=depth/2,g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute([-w,0,d,w,0,d,0,height,d,-w,0,-d,w,0,-d,0,height,-d],3));
  g.setIndex([0,1,2,5,4,3,0,2,5,0,5,3,2,1,4,2,4,5,0,3,4,0,4,1]);g.computeVertexNormals();return g;
}

/** 两个独立轮廓共用地面锚点；烘焙顶点色后每级住宅仅需一个实例批次。 */
export function gardenHouseGeometry(level:1|2,terraced=false):THREE.BufferGeometry {
  const pieces:THREE.BufferGeometry[]=[];
  const add=(geometry:THREE.BufferGeometry,x:number,y:number,z:number,color:string,rx=0,ry=0,rz=0)=>{
    geometry.rotateX(rx);geometry.rotateY(ry);geometry.rotateZ(rz);geometry.translate(x,y,z);
    const g=geometry.index?geometry.toNonIndexed():geometry;
    if(g!==geometry)geometry.dispose();
    g.deleteAttribute('uv');
    const c=new THREE.Color(color),attribute=g.getAttribute('position');
    g.setAttribute('color',new THREE.Float32BufferAttribute(Array.from({length:attribute.count},()=>[c.r,c.g,c.b]).flat(),3));pieces.push(g);
  };
  const box=(x:number,y:number,z:number,w:number,h:number,d:number,c:string,rz=0)=>add(new THREE.BoxGeometry(w,h,d),x,y,z,c,0,0,rz);
  const flowerBox=(x:number,y:number,z:number)=>{
    box(x,y,z,.28,.075,.12,'#dda16c');
    for(const dx of [-.08,0,.08]){add(new THREE.IcosahedronGeometry(.055,0),x+dx,y+.06,z,'#86ac62');add(new THREE.IcosahedronGeometry(.027,1),x+dx,y+.105,z+.025,'#f3b99a');}
  };
  const frontWindow=(x:number,y:number,z:number,w=.25,h=.27)=>{
    box(x,y,z,w+.065,h+.065,.045,'#fff9df');box(x,y,z+(z<0?-.027:.027),w,h,.018,'#81c4d5');
    box(x,y,z+(z<0?-.042:.042),.022,h,.015,'#fff4d3');box(x,y,z+(z<0?-.043:.043),w,.022,.015,'#fff4d3');
  };
  if(terraced){
    const height=level===1?.68:1.3,roof=level===1?'#e98460':'#6da7a8';
    box(0,height/2,-.04,2,height,.86,'#fff0d1');
    box(0,.055,-.04,2,.11,.88,'#e7cba0');
    // 连续横脊在地界处精确接合；不靠重叠屋檐或跨空地连接体掩盖分户边界。
    add(gable(1.08,2,.32),0,height,-.04,roof,0,Math.PI/2);
    box(0,height+.32,-.04,2,.035,.035,level===1?'#f7b280':'#acd1bf');
    box(0,height+.015,.5,2,.05,.035,'#f4ddb7');
    box(0,height+.015,-.58,2,.05,.035,'#f4ddb7');
    for(const x of [-.82,-.55,-.28,0,.28,.55,.82]){
      add(new THREE.BoxGeometry(.016,.02,.63),x,height+.16,.23,roof,.54);
      add(new THREE.BoxGeometry(.016,.02,.63),x,height+.16,-.31,roof,-.54);
    }
    box(-.37,.25,.407,.25,.5,.035,'#bda16b');
    frontWindow(.35,.36,.405,.48,.3);
    frontWindow(-.45,.36,-.48,.38,.29);frontWindow(.45,.36,-.48,.38,.29);
    flowerBox(.35,.17,.48);
    if(level===2){
      box(0,.72,-.04,2,.06,.9,'#f8ddb4');
      frontWindow(-.38,1.04,.405,.38,.34);frontWindow(.38,1.04,.405,.38,.34);
      frontWindow(-.4,1.04,-.48,.36,.3);frontWindow(.4,1.04,-.48,.36,.3);
      box(0,.78,.48,1.52,.06,.29,'#fff6d9');
      for(const x of [-.73,-.49,-.25,0,.25,.49,.73])box(x,.935,.615,.025,.25,.025,'#faf2d2');
      box(0,1.07,.615,1.52,.035,.035,'#faf2d2');
      for(const x of [-.73,.73])box(x,.95,.49,.025,.26,.25,'#faf2d2');
      flowerBox(.4,.87,.61);
    }else{
      box(-.37,.57,.48,.62,.045,.25,'#85b9ad');
      for(const x of [-.65,-.1])box(x,.27,.56,.035,.54,.035,'#faf3d9');
    }
    for(const x of [-.99,.99]){
      box(x,height/2,-.04,.02,height,.86,'#ead4ab');
      for(const y of level===1?[.36]:[.36,1.04]){
        box(x,y,-.08,.02,.31,.32,'#fff9df');
        box(Math.sign(x)*.995,y,-.08,.01,.24,.25,'#81c4d5');
      }
    }
  }else if(level===1){
    box(0,.34,-.035,.94,.68,.79,'#fff0cc');
    box(0,.065,-.035,.97,.13,.82,'#ead4ab');
    add(gable(1.12,.99,.36),0,.69,-.035,'#e98460');
    box(0,1.055,-.035,.035,.035,1.01,'#f7b280');
    for(const x of [-.42,-.28,-.14,.14,.28,.42])box(x,.705+.36*(1-Math.abs(x)/.56),-.035,.015,.015,1,'#f2a374');
    box(-.16,.23,.373,.22,.46,.035,'#b8a16a');
    add(new THREE.SphereGeometry(.025,8,6),-.09,.23,.397,'#e8bf62');
    frontWindow(.235,.39,.377,.25,.28);
    box(-.19,.57,.48,.51,.055,.26,'#85b9ad',-.05);
    for(const x of [-.42,.04])box(x,.27,.56,.035,.54,.035,'#faf3d9');
    box(-.19,.035,.5,.46,.07,.23,'#f2d9ae');
    box(-.49,.38,-.12,.025,.3,.29,'#fff9df');box(-.505,.38,-.12,.018,.23,.22,'#81c4d5');
    box(.47,.37,-.14,.026,.3,.3,'#fff9df');box(.488,.37,-.14,.018,.23,.23,'#81c4d5');
    box(-.27,.98,-.22,.13,.3,.15,'#fff0cc');box(-.27,1.14,-.22,.17,.045,.19,'#d9815f');
    flowerBox(.23,.17,.44);frontWindow(0,.37,-.445,.3,.27);
  }else{
    box(0,.65,-.04,1,1.3,.86,'#fff0d1');
    box(0,.08,-.04,1.035,.16,.89,'#e7cba0');
    box(0,.72,-.04,1.04,.07,.91,'#f8ddb4');
    add(gable(1.18,1.08,.36),0,1.315,-.04,'#6da7a8');
    box(0,1.68,-.04,.04,.04,1.11,'#acd1bf');
    for(const x of [-.44,-.29,-.145,.145,.29,.44])box(x,1.33+.36*(1-Math.abs(x)/.59),-.04,.016,.016,1.09,'#8ebfba');
    box(-.24,.25,.407,.22,.5,.035,'#bda16b');frontWindow(.235,.36,.405,.25,.3);
    frontWindow(-.23,1.045,.405,.22,.35);frontWindow(.23,1.045,.405,.22,.35);
    box(0,.78,.48,.98,.07,.29,'#fff6d9');
    for(const x of [-.46,-.3,-.15,0,.15,.3,.46])box(x,.935,.615,.026,.25,.026,'#faf2d2');
    box(0,1.07,.615,1,.035,.035,'#faf2d2');box(0,.84,.615,1,.03,.03,'#faf2d2');
    for(const x of [-.48,.48])box(x,.95,.49,.026,.26,.25,'#faf2d2');
    for(const x of [-.46,.46])box(x,.38,.57,.035,.76,.035,'#fff5d7');
    box(.51,1.02,-.12,.024,.33,.32,'#fff9df');box(.528,1.02,-.12,.018,.26,.25,'#81c4d5');
    box(-.51,1.02,-.12,.024,.33,.32,'#fff9df');box(-.528,1.02,-.12,.018,.26,.25,'#81c4d5');
    box(-.27,1.49,.3,.28,.26,.28,'#fff0d1');add(gable(.38,.36,.17),-.27,1.62,.3,'#6da7a8');frontWindow(-.27,1.51,.45,.15,.15);
    box(.28,1.56,-.29,.14,.38,.16,'#fff0d1');box(.28,1.76,-.29,.18,.04,.2,'#d98e6c');
    frontWindow(-.24,.36,-.48,.23,.29);frontWindow(.24,.36,-.48,.23,.29);
    frontWindow(-.24,1.045,-.48,.23,.29);frontWindow(.24,1.045,-.48,.23,.29);
    flowerBox(-.24,.87,.61);flowerBox(.25,.17,.48);
  }
  const merged=mergeGeometries(pieces)!;pieces.forEach(g=>g.dispose());merged.computeBoundingBox();merged.computeBoundingSphere();return merged;
}
