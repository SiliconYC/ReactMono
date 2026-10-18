import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Suspense, useLayoutEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import type { GameState } from "../../core/game.js";
import { RentTransfer } from "./RentTransfer.js";
import { OutcomeCelebration } from "./OutcomeCelebration.js";
import type { OutcomeCue } from "../outcomes.js";
import type { RentCue } from "../presentation.js";
import { Mascot, type MotionCue } from "./Mascot.js";
import { MiniatureTown } from "./MiniatureTown.js";
import { cameraFrame, type ViewportInsets } from "./camera-layout.js";
import { ACTOR_ANCHOR_Y, positionForTile } from "./layout.js";

type WorldCanvasProps = Readonly<{
  game: GameState;
  motion: MotionCue | null;
  dieValue: number | null;
  dieNonce: number;
  reducedMotion: boolean;
  followCurrent: boolean;
  rent: RentCue | null;
  outcome?: OutcomeCue | null;
  pendingBankruptIds?: readonly string[];
  paused?: boolean;
  viewportInsets?: ViewportInsets;
  onMotionComplete: () => void;
  onActorStep: (tileId: number) => void;
  onSelectTile?: (tileId: number) => void;
}>;

function CameraRig({
  target,
  follow,
  reducedMotion,
  insets,
  map,
}: {
  target: THREE.Vector3;
  follow: boolean;
  reducedMotion: boolean;
  insets?: ViewportInsets;
  map: GameState["map"];
}): null {
  const { camera, size } = useThree();
  const initialized = useRef(false);
  const look = useMemo(() => new THREE.Vector3(), []);
  const desired = useMemo(() => new THREE.Vector3(), []);
  const framed = useMemo(() => new THREE.Vector3(), []);
  const right = useMemo(() => new THREE.Vector3(1, 0, -1).normalize(), []);
  const up = useMemo(
    () =>
      new THREE.Vector3(
        -10.2,
        Math.hypot(10.2, 10.2) ** 2 / 12.2,
        -10.2,
      ).normalize(),
    [],
  );
  useFrame((_, delta) => {
    const blend =
      reducedMotion || !initialized.current ? 1 : 1 - Math.exp(-5 * delta);
    const frame = cameraFrame(
      size,
      insets,
      follow
        ? { width: 9, depth: 7 }
        : { width: map.columns * 2 + 3, depth: map.rows * 2 + 3 },
    );
    if (camera instanceof THREE.OrthographicCamera) {
      camera.zoom = THREE.MathUtils.lerp(
        camera.zoom,
        Math.min(frame.zoom, 64),
        blend,
      );
      desired.set(follow ? target.x : 0, 0.3, follow ? target.z : 0);
      desired
        .addScaledVector(right, -frame.offsetX / camera.zoom)
        .addScaledVector(up, -frame.offsetY / camera.zoom);
      look.lerp(desired, blend);
      framed.set(10.2, 12.2, 10.2).add(look);
      camera.position.copy(framed);
      camera.lookAt(look);
      camera.updateProjectionMatrix();
      initialized.current = true;
    }
  });
  return null;
}

function Scene(props: WorldCanvasProps): React.JSX.Element {
  const invalidate = useThree((state) => state.invalidate);
  const scene = useThree((state) => state.scene);
  useLayoutEffect(() => {
    // Three.js does not inherit shadow flags from parent groups. Apply one
    // scene-wide rule so height, mesh role, and material never create exceptions.
    scene.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        object.castShadow = true;
        object.receiveShadow = true;
      }
    });
    // Imperative actor/camera targets and useFrame callbacks are not host props;
    // request a demand frame after their layout effects have synchronized them.
    invalidate();
  }, [
    scene,
    invalidate,
    props.game,
    props.motion,
    props.rent,
    props.outcome,
    props.followCurrent,
    props.reducedMotion,
    props.paused,
    props.viewportInsets,
  ]);
  const actor = props.game.players[props.game.currentPlayerIndex];
  const focusId =
    props.outcome?.stage === "draw"
      ? null
      : (props.outcome?.actorId ??
        props.motion?.actorId ??
        props.rent?.fromId ??
        actor.id);
  const focusActor =
    props.game.players.find((player) => player.id === focusId) ?? actor;
  const point = positionForTile(focusActor.position, props.game.map);
  const trackedPosition = useMemo(
    () => new THREE.Vector3(point.x, ACTOR_ANCHOR_Y, point.z),
    [],
  );
  return (
    <>
      <color attach="background" args={["#bfe6d9"]} />
      <fog attach="fog" args={["#bfe6d9", 35, 65]} />
      <ambientLight intensity={1.35} color="#dff7ef" />
      <hemisphereLight args={["#eafcf5", "#52756b", 1.25]} />
      <directionalLight
        position={[-8, 15, 7]}
        intensity={2.45}
        color="#fff0c5"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
        shadow-camera-near={10}
        shadow-camera-far={28}
        shadow-intensity={0.58}
        shadow-bias={-0.0001}
        shadow-normalBias={0.012}
        shadow-radius={3}
      />
      <CameraRig
        target={trackedPosition}
        follow={props.followCurrent && props.outcome?.stage !== "draw"}
        reducedMotion={props.reducedMotion}
        insets={props.viewportInsets}
        map={props.game.map}
      />
      <MiniatureTown game={props.game} onSelectTile={props.onSelectTile} />
      {props.game.players.map((player, seat) => (
        <Mascot
          key={player.id}
          id={player.id}
          seat={seat}
          tileId={player.position}
          map={props.game.map}
          active={player.id === focusId}
          bankrupt={player.bankrupt}
          awaitingExit={props.pendingBankruptIds?.includes(player.id) ?? false}
          outcome={props.outcome}
          motion={props.motion}
          reducedMotion={props.reducedMotion}
          onMotionComplete={props.onMotionComplete}
          onStep={props.onActorStep}
          dieValue={props.dieValue}
          dieNonce={props.dieNonce}
          trackedPosition={trackedPosition}
        />
      ))}
      {props.outcome && (
        <OutcomeCelebration
          key={`${props.outcome.stage}-${props.outcome.actorId}-${props.outcome.nonce}`}
          game={props.game}
          cue={props.outcome}
          reducedMotion={props.reducedMotion}
        />
      )}
      {props.rent && (
        <RentTransfer
          game={props.game}
          cue={props.rent}
          reducedMotion={props.reducedMotion}
        />
      )}
    </>
  );
}

export function WorldCanvas(props: WorldCanvasProps): React.JSX.Element {
  const [ready, setReady] = useState(false);
  // A financial modal has no visible scene interaction. Reduced-motion idle
  // scenes only need a fresh frame when React changes the game or camera.
  const frameLoop = props.paused
    ? "never"
    : props.reducedMotion && !props.motion && !props.rent && !props.outcome
      ? "demand"
      : "always";
  return (
    <div
      className="canvas-shell"
      data-ready={String(ready)}
      data-frameloop={frameLoop}
      data-safe-insets={
        props.viewportInsets ? JSON.stringify(props.viewportInsets) : undefined
      }
    >
      {!ready && (
        <div className="scene-loading" role="status">
          <span />
          正在搭建晴湾小镇…
        </div>
      )}
      <Canvas
        aria-label="晴湾小镇 3D 棋盘"
        data-testid="world-canvas"
        orthographic
        frameloop={frameLoop}
        shadows="variance"
        dpr={[1, 1.6]}
        camera={{ position: [10.2, 12.5, 10.2], zoom: 48, near: 0.1, far: 80 }}
        gl={{
          antialias: true,
          alpha: false,
          powerPreference: "high-performance",
        }}
        onCreated={() => setReady(true)}
        fallback={
          <div className="scene-error" role="status">
            <strong>当前浏览器无法建立 3D 场景</strong>
            <span>仍可从下方列表查看地块，并使用原有回合操作继续游戏。</span>
            <div className="scene-fallback-grid">
              {props.game.tiles.map((tile) => (
                <button
                  key={tile.id}
                  type="button"
                  onClick={() => props.onSelectTile?.(tile.id)}
                >
                  {tile.id + 1} · {tile.title}
                </button>
              ))}
            </div>
          </div>
        }
      >
        <Suspense fallback={null}>
          <Scene {...props} />
        </Suspense>
      </Canvas>
    </div>
  );
}
