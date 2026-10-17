import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Suspense, useMemo } from 'react';
import * as THREE from 'three';
import type { GameState } from '../../core/game.js';
import { Dice } from './Dice.js';
import { Mascot, type MotionCue } from './Mascot.js';
import { MiniatureTown } from './MiniatureTown.js';
import { positionForTile } from './layout.js';

type WorldCanvasProps = Readonly<{
  game: GameState;
  motion: MotionCue | null;
  dieValue: number | null;
  dieNonce: number;
  reducedMotion: boolean;
  followCurrent: boolean;
  onMotionComplete: () => void;
  onActorStep: (tileId: number) => void;
}>;

function CameraRig({ game, follow }: { game: GameState; follow: boolean }): null {
  const { camera } = useThree();
  const desired = useMemo(() => new THREE.Vector3(), []);
  const look = useMemo(() => new THREE.Vector3(), []);
  useFrame(() => {
    const actor = game.players[game.currentPlayerIndex];
    const point = actor === undefined ? { x: 0, z: 0 } : positionForTile(actor.position);
    const focusX = follow ? point.x * 0.16 : 0;
    const focusZ = follow ? point.z * 0.16 : 0;
    look.lerp(desired.set(focusX, 0.25, focusZ), 0.035);
    camera.position.lerp(desired.set(10.2 + look.x, 12.5, 10.2 + look.z), 0.035);
    camera.lookAt(look);
    camera.updateProjectionMatrix();
  });
  return null;
}

function Scene(props: WorldCanvasProps): React.JSX.Element {
  return (
    <>
      <color attach="background" args={['#bfe6d9']} />
      <fog attach="fog" args={['#bfe6d9', 18, 31]} />
      <ambientLight intensity={1.35} color="#dff7ef" />
      <hemisphereLight args={['#eafcf5', '#52756b', 1.25]} />
      <directionalLight
        position={[-8, 15, 7]}
        intensity={2.45}
        color="#fff0c5"
        castShadow
        shadow-mapSize-width={1536}
        shadow-mapSize-height={1536}
        shadow-camera-left={-12}
        shadow-camera-right={12}
        shadow-camera-top={12}
        shadow-camera-bottom={-12}
        shadow-bias={-0.0003}
      />
      <CameraRig game={props.game} follow={props.followCurrent} />
      <MiniatureTown game={props.game} />
      {props.game.players.map((player, seat) => (
        <Mascot
          key={player.id}
          id={player.id}
          seat={seat}
          tileId={player.position}
          active={seat === props.game.currentPlayerIndex}
          motion={props.motion}
          reducedMotion={props.reducedMotion}
          onMotionComplete={props.onMotionComplete}
          onStep={props.onActorStep}
        />
      ))}
      <Dice value={props.dieValue} nonce={props.dieNonce} />
    </>
  );
}

export function WorldCanvas(props: WorldCanvasProps): React.JSX.Element {
  return (
    <Canvas
      aria-label="晴湾小镇 3D 棋盘"
      data-testid="world-canvas"
      orthographic
      shadows
      dpr={[1, 1.6]}
      camera={{ position: [10.2, 12.5, 10.2], zoom: 48, near: 0.1, far: 80 }}
      gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
      fallback={<div role="alert">此浏览器暂时无法建立 3D 场景，请启用 WebGL 后重试。</div>}
    >
      <Suspense fallback={null}>
        <Scene {...props} />
      </Suspense>
    </Canvas>
  );
}

