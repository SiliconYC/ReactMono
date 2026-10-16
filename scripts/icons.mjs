/** 原创几何棋盘图标：不依赖绘图库，Node 内置 zlib 生成确定性 PNG。 */
import { deflateSync } from 'node:zlib';
import { writeFile, mkdir } from 'node:fs/promises';
const palette={dark:[16,38,34,255],green:[29,99,78,255],gold:[246,222,143,255],pale:[248,247,226,255]};
function crc32(buffer){
  let crc=0xffffffff;
  for(const byte of buffer){crc^=byte;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}
  return (crc^0xffffffff)>>>0;
}
function chunk(type,body){
  const name=Buffer.from(type,'ascii'),length=Buffer.alloc(4),sum=Buffer.alloc(4);
  length.writeUInt32BE(body.length);sum.writeUInt32BE(crc32(Buffer.concat([name,body])));
  return Buffer.concat([length,name,body,sum]);
}
function icon(size){
  const rgba=Buffer.alloc(size*size*4);
  const rectangle=(x,y,w,h,color)=>{
    const p=palette[color];
    for(let row=Math.floor(y*size);row<Math.ceil((y+h)*size);row++){
      for(let col=Math.floor(x*size);col<Math.ceil((x+w)*size);col++){
        if(col<0||row<0||col>=size||row>=size)continue;
        const i=(row*size+col)*4;for(let c=0;c<4;c++)rgba[i+c]=p[c];
      }
    }
  };
  rectangle(0,0,1,1,'dark');
  rectangle(.09,.09,.82,.82,'green');
  rectangle(.13,.13,.74,.035,'gold');rectangle(.13,.83,.74,.035,'gold');
  rectangle(.13,.13,.035,.735,'gold');rectangle(.835,.13,.035,.735,'gold');
  // 字形「富」：屋顶、横、田字、下部口形的原创像素几何造型。
  const stroke=.034;
  rectangle(.39,.255,.22,stroke,'pale');
  rectangle(.31,.30,.38,stroke,'pale');
  rectangle(.27,.30,stroke,.075,'pale');rectangle(.69-stroke,.30,stroke,.075,'pale');
  rectangle(.35,.395,.30,stroke,'pale');
  rectangle(.34,.46,.32,stroke,'pale');rectangle(.34,.46,stroke,.18,'pale');rectangle(.66-stroke,.46,stroke,.18,'pale');
  rectangle(.34,.61,.32,stroke,'pale');
  rectangle(.485,.46,stroke,.17,'pale');
  rectangle(.28,.70,.44,stroke,'pale');
  const scan=Buffer.alloc(size*(size*4+1));
  for(let row=0;row<size;row++)rgba.copy(scan,row*(size*4+1)+1,row*size*4,(row+1)*size*4);
  const header=Buffer.alloc(13);
  header.writeUInt32BE(size,0);header.writeUInt32BE(size,4);header[8]=8;header[9]=6;
  return Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),chunk('IHDR',header),chunk('IDAT',deflateSync(scan,{level:9})),chunk('IEND',Buffer.alloc(0))]);
}
export async function createIcons(){
  await mkdir('dist/icons',{recursive:true});
  for(const size of [192,512])await writeFile('dist/icons/icon-'+size+'.png',icon(size));
}
