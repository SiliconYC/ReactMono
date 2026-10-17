/** P4 #65: 4 original paper-art characters. Identity is the persisted seat index, never AI/human status. */
export const CHARACTER_NAMES = ['纸狐','圆熊','长耳兔','帆鸟'] as const;
export const CHARACTER_FILES = ['fox','bear','rabbit','bird'] as const;
export type CharacterMode = 'human'|'computer';
export type CharacterDisplay = 'pawn'|'portrait'|'badge'|'setup'|'winner';

/** Character assets have no network dependencies and are precached by the service worker. */
export function characterMarker(seat:number,kind:CharacterMode,display:CharacterDisplay,active=false,moving=false):unknown {
  const index=Math.max(0,Math.min(3,seat));
  const name=CHARACTER_NAMES[index],filename=CHARACTER_FILES[index];
  // Preserve legacy .piece / .portrait / .player-dot selectors for P1-P4 browser contracts.
  const legacy=display==='pawn'?`piece piece-${index+1}`:display==='portrait'?'portrait':
    display==='badge'?'player-dot':'';
  return <span className={`character-marker character-${index+1} character-${display} ${legacy} ${kind}${active?' character-active':''}${moving?' character-moving':''}`}
    data-character-seat={index+1} data-character-id={filename}
    title={`第 ${index+1} 位 · ${name} · ${kind==='computer'?'电脑':'真人'}`}
    aria-label={`第 ${index+1} 位${name}，${kind==='computer'?'电脑':'真人'}`}>
    <img className="character-image" src={`./art/character-${filename}.svg`} alt="" draggable={false}/>
    <span className="character-seat">{index+1}</span>
    {display!=='pawn'&&<span className="character-mode" aria-hidden="true">{kind==='computer'?'机':'人'}</span>}
  </span>;
}
