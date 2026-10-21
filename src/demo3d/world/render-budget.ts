export type RenderBudget=Readonly<{mode:'full'|'efficient';shadowSize:2048|1024;medianMs:number;samplesMs:readonly number[]}>;

export function chooseRenderBudget(samples:readonly number[]):RenderBudget|null {
  if(samples.length<5)return null;
  const sorted=samples.slice(-5).sort((a,b)=>a-b),medianMs=sorted[2];
  const efficient=medianMs>50;
  return {mode:efficient?'efficient':'full',shadowSize:efficient?1024:2048,medianMs,samplesMs:samples.slice(-5)};
}

export function renderPixelRatio(mode:RenderBudget['mode'],zoom:number,elevation:number,nativeDpr:number):number {
  const native=Math.max(1,Math.min(2,nativeDpr));
  // A distant road needs its original raster density; only larger projected
  // geometry can trade resolution for smooth camera and actor presentation.
  return mode==='efficient'&&1.78*zoom*Math.sin(elevation)>=4?.65:native;
}
