import { PostgameSummary, PostgameRanking } from './Postgame.js';
import { DebugTools } from './DebugTools.js';
import { setDebugCash, prepareDebugSimulation, MAX_DEBUG_ROUNDS, type DebugSimulationSetup } from '../core/debug-tools.js';
import { validateGameState } from '../core/save.js';
import type { DebugSimulationReply } from './debug-simulation.worker.js';
import { LevelPreview } from './LevelPreview.js';
import * as React from "react";
import { createRoot } from "react-dom/client";
import {
  applyAction,
  createGame,
  type GameAction,
  type CardKind,
  type GameEvent,
  type GameState,
  type Tile,
  type GameMap,
  type PlayerConfig,
  DEFAULT_CONFIG,
  netWorth,
  resaleValue,
  loanLimit,
  STOCKS,
  quoteMarket,
  type StockId,
  propertyVisitAvailable,
  propertyBlock,
  propertyRun,
  propertyRent,
  quotePropertyUpgrade,
} from "../core/game.js";
import { LEVELS, PLAYABLE_LEVELS, levelConfig } from "../core/level-data.js";
import { chooseComputerAction } from "../core/agent.js";
import {
  COMPUTER_STYLES,
  COMPUTER_STYLE_NAMES,
} from "../core/strategic-agent.js";
import {
  listSlots,
  readSlot,
  writeSlot,
  deleteSlot,
  type SlotSummary,
} from "../storage/indexeddb.js";
import {
  deserializeGame,
  MAX_SAVE_CHARS,
  type SaveEnvelope,
} from "../core/save.js";
import {
  Modal,
  SeatAvatar,
  TownIllustration,
  MeasuredWorld,
  compactCash,
} from "./game-ui.js";
import { MASCOT_SEAT_COLORS } from "../demo3d/world/seats.js";
import { eventCue, needsHumanHandoff, type VisualCue } from "./feedback.js";
import { SoundController } from "./audio.js";
import {
  cpuDelay,
  cpuTurnKey,
  addCpuTiming,
  initialCpuTiming,
  MAX_CPU_ACTIONS_PER_TURN,
  type CpuTiming,
} from "./computer-pace.js";
import type { MotionCue } from "../demo3d/world/Mascot.js";
import { rentCueFor, type RentCue } from "../demo3d/presentation.js";
import { outcomeSequence, type OutcomeCue } from "../demo3d/outcomes.js";

interface UiState {
  readonly sceneEpoch: number;
  readonly debugBusy: boolean;
  readonly debugMessage: string;
  readonly confirmText: string | null;
  readonly overlay:
    | "debug"
    | "results"
    | "menu"
    | "assets"
    | "bank"
    | "loan"
    | "stock"
    | "property"
    | "cards"
    | "saves"
    | "help"
    | "settings"
    | "tiles"
    | "events"
    | null;
  readonly dieActorId: string | null;
  readonly game: GameState;
  readonly displayGame: GameState;
  readonly message: string;
  readonly seedInput: string;
  readonly bankAmountInput: string;
  readonly stockAmountInput: string;
  readonly strategyDieInput: string;
  readonly roadblockTileInput: string;
  readonly playerSetup: readonly PlayerConfig[];
  readonly roundsInput: string;
  readonly endCondition: 'bankruptcy' | 'round_limit';
  readonly selectedMapId: string;
  readonly selectedTileId: number | null;
  readonly sceneReady: boolean;
  readonly lastMotion: {
    playerId: string;
    tileId: number;
    revision: number;
  } | null;
  readonly visualCue: VisualCue | null;
  readonly queuedRent: RentCue | null;
  readonly queuedOutcomes: readonly OutcomeCue[];
  readonly rentCue: RentCue | null;
  readonly outcomeCue: OutcomeCue | null;
  readonly outcomeQueue: readonly OutcomeCue[];
  readonly dieValue: number | null;
  readonly dieNonce: number;
  readonly setupScreen: "title" | "new-game" | "saves" | "help";
  readonly cameraFollow: boolean;
  readonly motionOff: boolean;
  readonly financePanel: "property" | "bank" | "loan" | "stock" | null;
  readonly awaitingHandoff: boolean;
  readonly fastMode: boolean;
  readonly cpuPaused: boolean;
  readonly cpuTiming: CpuTiming;
  readonly specialEnabled: boolean;
  readonly activeSeed: number | null;
  readonly saveSlots: readonly SlotSummary[];
  readonly saveStatus: string;
  readonly storageBusy: boolean;
  readonly importPreview: SaveEnvelope | null;
  readonly importName: string;
  readonly offline: boolean;
  readonly pwaUpdate: boolean;
  readonly pwaMessage: string;
}

class App extends React.Component<object, UiState> {
  constructor(props: object) {
    super(props);
    this.state = {
      sceneEpoch: 0,
      debugBusy: false,
      debugMessage: "",
      confirmText: null,
      overlay: null,
      dieActorId: null,
      game: createGame(20261015),
      displayGame: createGame(20261015),
      seedInput: "20261015",
      bankAmountInput: "100",
      stockAmountInput: "1",
      strategyDieInput: "1",
      roadblockTileInput: "1",
      playerSetup: [
        { id: "p1", name: "玩家", kind: "human" },
        { id: "p2", name: "电脑", kind: "computer", computerStyle: "balanced" },
      ],
      roundsInput: "60",
      endCondition: "bankruptcy",
      selectedMapId: "classic-24",
      selectedTileId: null,
      sceneReady: false,
      lastMotion: null,
      visualCue: null,
      queuedRent: null,
      queuedOutcomes: [],
      rentCue: null,
      outcomeCue: null,
      outcomeQueue: [],
      dieValue: null,
      dieNonce: 0,
      setupScreen: "title",
      cameraFollow:
        typeof localStorage === "undefined"
          ? false
          : localStorage.getItem("reactmono-camera-follow") === "1",
      motionOff:
        typeof localStorage === "undefined"
          ? false
          : localStorage.getItem("reactmono-motion-off") === "1",
      financePanel: null,
      awaitingHandoff: false,
      fastMode: false,
      cpuPaused: false,
      cpuTiming: initialCpuTiming,
      specialEnabled: false,
      activeSeed: null,
      saveSlots: [],
      saveStatus: "正在读取本地存档…",
      storageBusy: false,
      importPreview: null,
      importName: "",
      offline: typeof navigator === "undefined" ? false : !navigator.onLine,
      pwaUpdate: false,
      pwaMessage: "",
      message: "",
    };
  }

  private debugWorker: Worker | null = null;
  private debugRequestId = 0;
  private debugTimeout: number | null = null;
  private terminateDebugWorker = (): void => {
    this.debugRequestId++;
    this.debugWorker?.terminate();
    this.debugWorker = null;
    if (this.debugTimeout !== null) window.clearTimeout(this.debugTimeout);
    this.debugTimeout = null;
  };
  private cancelDebugSimulation = (): void => {
    this.terminateDebugWorker();
    this.setState({ debugBusy: false, debugMessage: "已取消模拟，原对局保持不变。" });
  };
  private setPlayerDebugCash = (playerId: string, cash: number): void => {
    if (this.debugWorker || this.state.debugBusy || this.state.storageBusy) return;
    const game = setDebugCash(this.state.game, playerId, cash);
    this.stopTimer();
    this.cancelCue();
    this.clearWorldTimer();
    this.setState({
      game, displayGame: game, lastMotion: null, visualCue: null,
      queuedRent: null, queuedOutcomes: [], rentCue: null, outcomeCue: null, outcomeQueue: [],
      dieValue: null, dieActorId: null,
      debugMessage: (game.players.find(player => player.id === playerId)?.name ?? "玩家") + "现金已设置为 " + cash.toLocaleString("zh-CN") + "。",
    });
  };
  private simulateDebugGame = (rounds: number, setup:DebugSimulationSetup = {}): void => {
    if (this.debugWorker || this.state.debugBusy || this.state.storageBusy) return;
    if (!Number.isSafeInteger(rounds) || rounds < 1 || rounds > MAX_DEBUG_ROUNDS)
      throw new Error("请输入有效的模拟轮数");
    if (this.state.game.status !== "playing") throw new Error("仅进行中的对局可以模拟");
    const snapshot = this.state.game;
    const input = prepareDebugSimulation(snapshot,setup);
    this.stopTimer();
    this.cancelCue();
    this.clearWorldTimer();
    const worker = new Worker(new URL('./debug-simulation.worker.ts', import.meta.url), { type: 'module' });
    this.debugWorker = worker;
    const requestId = ++this.debugRequestId;
    const isCurrent = (): boolean => this.debugWorker === worker && this.debugRequestId === requestId && this.state.game === snapshot;
    const fail = (error: string): void => {
      if (!isCurrent()) return;
      this.terminateDebugWorker();
      this.setState({ debugBusy: false, debugMessage: "模拟失败：" + error + "。原对局未被修改。" });
    };
    worker.onmessage = (event: MessageEvent<DebugSimulationReply>) => {
      if (!isCurrent() || event.data.requestId !== requestId) return;
      const reply = event.data;
      if (!reply.ok) { fail(reply.error); return; }
      try { validateGameState(reply.result.state); }
      catch (error) { fail(error instanceof Error ? error.message : String(error)); return; }
      const game = reply.result.state;
      this.terminateDebugWorker();
      this.cpuTurnMark = "";
      this.cpuTurnActions = 0;
      this.lastCpuEvents = [];
      this.lastCommittedAction = null;
      // 批量快照重挂载整个场景，避免把模拟期间的产权和等级差异当作现场建设动画。
      this.setState(state => ({
        game, displayGame: game, sceneEpoch: state.sceneEpoch + 1, sceneReady: false,
        overlay: game.status === "finished" ? null : state.overlay,
        debugBusy: false, lastMotion: null, visualCue: null, selectedTileId: null,
        queuedRent: null, queuedOutcomes: [], rentCue: null, outcomeCue: null, outcomeQueue: [],
        dieValue: null, dieActorId: null, financePanel: null,
        awaitingHandoff: game.status === "playing" && game.players[game.currentPlayerIndex].kind === "human",
        debugMessage: "模拟完成：第 " + snapshot.round + " 轮 → 第 " + game.round + " 轮，执行 " + reply.result.actions + " 个动作。" + (game.status === "finished" ? "对局已结束。" : ""),
        message: game.status === "finished" ? "后台模拟完成，对局已结束。" : "后台模拟完成，请确认当前玩家后继续。",
      }));
    };
    worker.onerror = event => { event.preventDefault(); fail("后台计算异常，请重试或减少轮数"); };
    worker.onmessageerror = () => fail("后台结果无法读取");
    this.debugTimeout = window.setTimeout(() => fail("后台计算超时，请减少轮数"), 30_000);
    this.setState({
      debugBusy: true, debugMessage: "正在后台模拟，原对局将在成功后一次性更新…",
      displayGame: snapshot, lastMotion: null, visualCue: null,
      queuedRent: null, queuedOutcomes: [], rentCue: null, outcomeCue: null, outcomeQueue: [],
      dieValue: null, dieActorId: null,
    });
    try { worker.postMessage({ requestId, game: input, rounds }); }
    catch (error) { fail(error instanceof Error ? error.message : String(error)); }
  };

  private computerTimer: number | null = null;
  private onSceneTileSelect = (tileId: number): void => {
    if (!this.state.overlay) this.setState({ selectedTileId: tileId });
  };
  private onActorStep = (tileId: number): void => {
    const cue = this.state.visualCue;
    if (!cue) return;
    const step = cue.path.indexOf(tileId) + 1;
    if (step > cue.step) {
      this.sound.play([
        { type: "player_moved", actorId: cue.actorId ?? undefined },
      ]);
      this.setState({ visualCue: { ...cue, step } });
    }
  };
  private cpuTurnMark = "";
  private cpuTurnActions = 0;
  private lastCpuEvents: readonly GameEvent[] = [];
  private toggleCpuPause = (): void => {
    const cpuPaused = !this.state.cpuPaused;
    this.stopTimer();
    this.setState({
      cpuPaused,
      message: cpuPaused ? "电脑已暂停，点击继续即可恢复。" : "电脑继续行动。",
    });
  };
  private toggleCpuFast = (): void => {
    this.stopTimer();
    const fastMode = !this.state.fastMode;
    if (fastMode && this.state.visualCue?.path.length) {
      const rent = this.state.queuedRent,
        outcomes = this.state.queuedOutcomes;
      this.cancelCue();
      this.setState(
        { fastMode, displayGame: this.state.game, visualCue: null },
        () => this.playWorldSequence(rent, outcomes),
      );
    } else this.setState({ fastMode });
  };
  private sound = new SoundController();
  private cueTimer: number | null = null;
  private worldTimer: number | null = null;
  private cueGeneration = 0;
  private get noMotion(): boolean {
    return (
      this.state.motionOff ||
      this.state.fastMode ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }
  private cancelCue = (): void => {
    this.cueGeneration++;
    if (this.cueTimer !== null) window.clearTimeout(this.cueTimer);
    this.cueTimer = null;
  };
  private onVisibility = (): void => {
    if (document.hidden) {
      this.stopTimer();
      this.cancelCue();
      this.clearWorldTimer();
      this.setState({
        displayGame: this.state.game,
        visualCue: null,
        queuedRent: null,
        queuedOutcomes: [],
        rentCue: null,
        outcomeCue: null,
        outcomeQueue: [],
      });
    } else this.setState({}); // resume only if the currently loaded state still belongs to a computer
  };
  private cueFor(
    before: GameState,
    after: GameState,
    events: readonly GameEvent[],
  ): VisualCue | null {
    this.cancelCue();
    if (this.noMotion || document.hidden) return null;
    const cue = eventCue(before, after, events);
    if (!cue) return null;
    const token = this.cueGeneration;
    // The world animation owns the movement clock. Keep the complete route
    // mounted until Mascot reports arrival; a timer here used to cut off long
    // paths before the 3D actor reached its destination.
    this.cueTimer = window.setTimeout(
      () => {
        if (token === this.cueGeneration) {
          if (cue.path.length) this.finishSceneMotion();
          else this.setState({ visualCue: null });
        }
      },
      cue.path.length ? 7000 : 1200,
    );
    return cue;
  }
  private dieStateFor(
    events: readonly GameEvent[],
  ): Pick<UiState, "dieValue" | "dieNonce" | "dieActorId"> {
    const roll = events.find((event) => event.type === "die_rolled");
    return roll
      ? {
          dieValue: Number(roll.details?.value),
          dieNonce: this.state.dieNonce + 1,
          dieActorId: roll.actorId ?? null,
        }
      : ({} as Pick<UiState, "dieValue" | "dieNonce" | "dieActorId">);
  }
  private toggleMotion = (): void => {
    const motionOff = !this.state.motionOff;
    try {
      localStorage.setItem("reactmono-motion-off", motionOff ? "1" : "0");
    } catch {}
    if (motionOff && this.state.visualCue?.path.length) {
      const rent = this.state.queuedRent,
        outcomes = this.state.queuedOutcomes;
      this.cancelCue();
      this.setState(
        { motionOff, displayGame: this.state.game, visualCue: null },
        () => this.playWorldSequence(rent, outcomes),
      );
    } else this.setState({ motionOff });
  };
  private finishSceneMotion = (): void => {
    if (this.state.visualCue !== null) {
      this.cancelCue();
      const rent = this.state.queuedRent,
        outcomes = this.state.queuedOutcomes;
      const landing = this.state.game.events
        .slice(this.state.displayGame.events.length)
        .filter(
          (e) =>
            ![
              "die_rolled",
              "player_moved",
              "rent_paid",
              "player_bankrupt",
              "game_finished",
            ].includes(e.type),
        );
      this.setState({ displayGame: this.state.game, visualCue: null }, () => {
        this.sound.play(landing);
        this.playWorldSequence(rent, outcomes, true);
      });
    }
  };
  private skipPresentation = (): void => {
    this.cancelCue();
    this.clearWorldTimer();
    this.setState({
      displayGame: this.state.game,
      visualCue: null,
      queuedRent: null,
      queuedOutcomes: [],
      rentCue: null,
      outcomeCue: null,
      outcomeQueue: [],
    });
  };
  private clearWorldTimer = (): void => {
    if (this.worldTimer !== null) window.clearTimeout(this.worldTimer);
    this.worldTimer = null;
  };
  private playWorldSequence = (
    rent: RentCue | null,
    outcomes: readonly OutcomeCue[],
    withAudio = false,
  ): void => {
    this.clearWorldTimer();
    const beginOutcomes = (): void => this.playNextOutcome(outcomes, withAudio);
    this.setState(
      {
        rentCue: this.noMotion ? null : rent,
        outcomeCue: null,
        outcomeQueue: outcomes,
        queuedRent: null,
        queuedOutcomes: [],
      },
      () => {
        if (rent && !this.noMotion) {
          if (withAudio) this.sound.play([{ type: "rent_paid" }]);
          this.worldTimer = window.setTimeout(() => {
            this.worldTimer = null;
            this.setState({ rentCue: null }, beginOutcomes);
          }, 1800);
        } else beginOutcomes();
      },
    );
  };
  private playNextOutcome = (
    outcomes: readonly OutcomeCue[],
    withAudio = false,
  ): void => {
    const [next, ...rest] = outcomes;
    if (!next) {
      this.setState({ outcomeCue: null, outcomeQueue: [] });
      return;
    }
    if (withAudio)
      this.sound.play([
        {
          type: next.stage === "bankrupt" ? "player_bankrupt" : "game_finished",
        },
      ]);
    this.setState({ outcomeCue: next, outcomeQueue: rest });
    this.worldTimer = window.setTimeout(
      () => {
        this.worldTimer = null;
        this.setState({ outcomeCue: null }, () =>
          this.playNextOutcome(rest, withAudio),
        );
      },
      this.noMotion ? 300 : next.stage === "bankrupt" ? 1800 : 2200,
    );
  };
  /** Ignore a rapid second tap against the same immutable turn state. */
  private lastCommittedAction: {
    game: GameState;
    signature: string;
    at: number;
  } | null = null;
  private manualSaveBusy = false;

  private saveEpoch = 0;
  private saveQueue: Promise<void> = Promise.resolve();

  private pwaRegistration: ServiceWorkerRegistration | null = null;
  private shouldReload = false;
  private updateOnline = (): void => {
    this.setState({ offline: !navigator.onLine });
  };
  private controllerChanged = (): void => {
    if (this.shouldReload) window.location.reload();
  };
  private checkUpdate = (reg: ServiceWorkerRegistration): void => {
    if (reg.waiting && navigator.serviceWorker.controller)
      this.setState({ pwaUpdate: true });
  };
  private initPwa = async (): Promise<void> => {
    if (import.meta.env.DEV) {
      const registration = await navigator.serviceWorker?.getRegistration();
      if (registration) await registration.unregister();
      this.setState({ pwaMessage: "开发预览不启用离线缓存。" });
      return;
    }
    if (!("serviceWorker" in navigator)) {
      this.setState({ pwaMessage: "本浏览器不支持应用安装，仍可在线游玩。" });
      return;
    }
    try {
      navigator.serviceWorker.addEventListener(
        "controllerchange",
        this.controllerChanged,
      );
      const reg = await navigator.serviceWorker.register("./sw.js", {
        scope: "./",
      });
      this.pwaRegistration = reg;
      reg.addEventListener("updatefound", () => {
        const worker = reg.installing;
        worker?.addEventListener("statechange", () => {
          if (worker.state === "installed") this.checkUpdate(reg);
        });
      });
      this.checkUpdate(reg);
    } catch (e) {
      this.setState({
        pwaMessage:
          "离线缓存安装失败，在线游戏仍可使用：" +
          (e instanceof Error ? e.message : String(e)),
      });
    }
  };
  private applyPwaUpdate = async (): Promise<void> => {
    const worker = this.pwaRegistration?.waiting;
    if (!worker) return;
    await this.saveQueue;
    this.shouldReload = true;
    worker.postMessage("SKIP_WAITING");
  };
  componentDidMount(): void {
    void this.refreshSlots();
    window.addEventListener("online", this.updateOnline);
    document.addEventListener("visibilitychange", this.onVisibility);
    window.addEventListener("offline", this.updateOnline);
    void this.initPwa();
  }
  private stopTimer(): void {
    if (this.computerTimer !== null) {
      window.clearTimeout(this.computerTimer);
      this.computerTimer = null;
    }
  }
  private refreshSlots = async (): Promise<void> => {
    try {
      const saveSlots = await listSlots();
      this.setState({
        saveSlots,
        saveStatus:
          this.state.saveStatus === "正在读取本地存档…"
            ? "本地存档已就绪"
            : this.state.saveStatus,
      });
    } catch (e) {
      this.setState({
        saveStatus:
          "本地存储不可用：" +
          (e instanceof Error ? e.message : String(e)) +
          "。请检查无痕模式或磁盘空间。",
      });
    }
  };
  /**
   * An active fast AI game can change state much faster than IndexedDB commits.
   * Persist the latest immutable snapshot, not every obsolete intermediate step.
   * The latest write completes before a PWA update or save restore via saveQueue.
   */
  private pendingAutosave: { game: GameState; epoch: number } | null = null;
  private autosaveDraining = false;
  private scheduleAutosave(game: GameState): void {
    this.pendingAutosave = { game, epoch: this.saveEpoch };
    if (this.autosaveDraining) return;
    this.autosaveDraining = true;
    this.saveQueue = this.saveQueue.then(async () => {
      try {
        while (this.pendingAutosave) {
          const item = this.pendingAutosave;
          this.pendingAutosave = null;
          if (item.epoch !== this.saveEpoch) continue;
          try {
            await writeSlot("auto", "自动存档", "auto", item.game);
            if (item.epoch !== this.saveEpoch) continue;
            if (
              this.state.saveStatus === "本地存档已就绪" ||
              this.state.saveStatus.startsWith("自动保存成功")
            )
              this.setState({
                saveStatus: "自动保存成功 · 第 " + item.game.round + " 轮",
              });
            await this.refreshSlots();
          } catch (e) {
            if (item.epoch === this.saveEpoch)
              this.setState({
                saveStatus:
                  "自动保存失败：" +
                  (e instanceof Error ? e.message : String(e)) +
                  "。请手动导出备份。",
              });
          }
        }
      } finally {
        this.autosaveDraining = false;
      }
    });
  }

  private exportSlot = async (slot: SlotSummary): Promise<void> => {
    try {
      const backup = await readSlot(slot.id);
      const content = JSON.stringify(backup, null, 2);
      const blob = new Blob([content], {
        type: "application/json;charset=utf-8",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      const filename = slot.name.replace(/[\\/:*?"<>|]/g, "_");
      link.href = url;
      link.download =
        "存档-" +
        filename +
        "-" +
        backup.updatedAt.slice(0, 10).replaceAll("-", "") +
        ".json";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      this.setState({
        saveStatus: "已生成「" + slot.name + "」备份文件，请自行保管。",
      });
    } catch (e) {
      this.setState({
        saveStatus: "导出失败：" + (e instanceof Error ? e.message : String(e)),
      });
    }
  };
  private selectImport = async (event: {
    target: { files: FileList | null; value: string };
  }): Promise<void> => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    this.setState({ importPreview: null });
    if (file.size > MAX_SAVE_CHARS) {
      this.setState({ saveStatus: "导入失败：文件过大，最多 4 MB" });
      return;
    }
    try {
      const raw = await file.text();
      const preview = deserializeGame(raw);
      const filename = file.name
        .replace(/^存档-(.*)-[0-9]{8}\.json$/i, "$1")
        .replace(/\.json$/i, "");
      const name = (filename.trim() || "导入存档").slice(0, 60);
      this.setState({
        importPreview: preview,
        importName: name,
        saveStatus: "文件校验通过，请预览并选择导入方式。",
      });
    } catch (e) {
      this.setState({
        saveStatus:
          "导入失败：" +
          (e instanceof Error ? e.message : String(e)) +
          "。原存档未改动。",
      });
    }
  };
  private applyImport = async (mode: "new" | "overwrite"): Promise<void> => {
    const { importPreview, saveSlots } = this.state;
    if (!importPreview || this.state.storageBusy) return;
    const name = this.state.importName.trim();
    if (!name || name.length > 60) {
      this.setState({ saveStatus: "请输入 1 至 60 个字符的存档名称" });
      return;
    }
    const duplicate = saveSlots.find((s) => s.name === name);
    if (mode === "overwrite" && !duplicate) return;
    const id =
      mode === "overwrite" && duplicate
        ? duplicate.id
        : "manual-" + crypto.randomUUID();
    const newName = mode === "new" && duplicate ? name + "（副本）" : name;
    if (newName.length > 60) {
      this.setState({ saveStatus: "副本名称过长，请先缩短名称" });
      return;
    }
    try {
      await writeSlot(id, newName, "manual", importPreview.game);
      this.setState({
        importPreview: null,
        importName: "",
        saveStatus: "「" + newName + "」已安全导入，可点击读取继续对局。",
      });
      await this.refreshSlots();
    } catch (e) {
      this.setState({
        saveStatus:
          "写入失败：" +
          (e instanceof Error ? e.message : String(e)) +
          "。原存档未被修改。",
      });
    }
  };

  private newManualSlot = async (): Promise<void> => {
    if (
      this.state.game.status === "setup" ||
      this.state.storageBusy ||
      this.manualSaveBusy
    )
      return;
    const name = window
      .prompt("输入新存档名称", "存档 " + new Date().toLocaleString("zh-CN"))
      ?.trim();
    if (!name) return;
    if (name.length > 60) {
      this.setState({ saveStatus: "名称最多 60 个字符" });
      return;
    }
    this.manualSaveBusy = true;
    this.setState({ saveStatus: "正在写入手动存档…" });
    try {
      await writeSlot(
        "manual-" + crypto.randomUUID(),
        name,
        "manual",
        this.state.game,
      );
      this.setState({ saveStatus: "手动存档「" + name + "」保存成功" });
      await this.refreshSlots();
    } catch (e) {
      this.setState({
        saveStatus:
          "手动保存失败：" + (e instanceof Error ? e.message : String(e)),
      });
    } finally {
      this.manualSaveBusy = false;
      this.setState({});
    }
  };
  private overwriteSlot = async (slot: SlotSummary): Promise<void> => {
    if (
      this.state.game.status === "setup" ||
      slot.kind !== "manual" ||
      this.state.storageBusy
    )
      return;
    if (!(await this.confirm("确定用当前对局覆盖「" + slot.name + "」吗？")))
      return;
    try {
      await writeSlot(slot.id, slot.name, "manual", this.state.game);
      this.setState({ saveStatus: "已覆盖「" + slot.name + "」" });
      await this.refreshSlots();
    } catch (e) {
      this.setState({
        saveStatus: "覆盖失败：" + (e instanceof Error ? e.message : String(e)),
      });
    }
  };
  private restoreSlot = async (
    slot: SlotSummary,
    confirm = true,
  ): Promise<void> => {
    void this.sound.activate();
    if (this.state.storageBusy) return;
    if (
      confirm &&
      !(await this.confirm(
        "读取「" + slot.name + "」将替换屏幕上的当前游戏，是否继续？",
      ))
    )
      return;
    this.terminateDebugWorker();
    this.saveEpoch++;
    this.stopTimer();
    this.cpuTurnMark = "";
    this.cpuTurnActions = 0;
    this.lastCpuEvents = [];
    this.setState({
      storageBusy: true,
      saveStatus: "正在读取「" + slot.name + "」…",
    });
    try {
      await this.saveQueue;
      const saved = await readSlot(slot.id);
      this.cancelCue();
      this.clearWorldTimer();
      this.setState({
        sceneEpoch: this.state.sceneEpoch + 1,
        sceneReady: false,
        debugBusy: false,
        game: saved.game,
        displayGame: saved.game,
        activeSeed: null,
        storageBusy: false,
        awaitingHandoff: false,
        overlay: null,
        financePanel: null,
        visualCue: null,
        queuedRent: null,
        queuedOutcomes: [],
        rentCue: null,
        outcomeCue: null,
        outcomeQueue: [],
        dieValue: null,
        dieActorId: null,
        setupScreen: "title",
        roundsInput: String(saved.game.maxRounds),
        endCondition: saved.game.endCondition??"round_limit",
        selectedMapId: saved.game.map.id,
        selectedTileId: null,
        lastMotion: null,
        playerSetup: saved.game.players.map((p) => ({
          id: p.id,
          name: p.name,
          kind: p.kind,
          ...(p.computerStyle ? { computerStyle: p.computerStyle } : {}),
        })),
        saveStatus: "已读取「" + slot.name + "」",
        message: "已恢复第 " + saved.game.round + " 轮，可从当前阶段继续。",
      });
    } catch (e) {
      this.setState({
        storageBusy: false,
        saveStatus:
          "读档失败：" +
          (e instanceof Error ? e.message : String(e)) +
          "。原对局未被修改。",
      });
    }
  };
  private removeSlot = async (slot: SlotSummary): Promise<void> => {
    if (
      this.state.storageBusy ||
      !(await this.confirm("确定永久删除「" + slot.name + "」吗？"))
    )
      return;
    try {
      await deleteSlot(slot.id);
      this.setState({ saveStatus: "已删除「" + slot.name + "」" });
      await this.refreshSlots();
    } catch (e) {
      this.setState({
        saveStatus: "删除失败：" + (e instanceof Error ? e.message : String(e)),
      });
    }
  };

  reset = (): void => {
    this.terminateDebugWorker();
    this.saveEpoch++;
    this.stopTimer();
    this.cancelCue();
    this.clearWorldTimer();
    this.cpuTurnMark = "";
    this.cpuTurnActions = 0;
    this.lastCpuEvents = [];
    const base =
      levelConfig(LEVELS.some(level => level.map.id === this.state.selectedMapId) ? this.state.selectedMapId : "classic-24");
    const fresh = createGame(20261015, base);
    this.setState({
      sceneEpoch: this.state.sceneEpoch + 1,
      sceneReady: false,
      debugBusy: false,
      game: fresh,
      displayGame: fresh,
      activeSeed: null,
      endCondition: "bankruptcy",
      selectedTileId: null,
      lastMotion: null,
      visualCue: null,
      queuedRent: null,
      queuedOutcomes: [],
      rentCue: null,
      outcomeCue: null,
      outcomeQueue: [],
      dieValue: null,
      dieActorId: null,
      overlay: null,
      setupScreen: "title",
      financePanel: null,
      awaitingHandoff: false,
      message: "已返回游戏首页。",
    });
  };
  private setCameraFollow = (cameraFollow:boolean): void => {
    if(this.state.cameraFollow===cameraFollow)return;
    try {
      localStorage.setItem("reactmono-camera-follow", cameraFollow ? "1" : "0");
    } catch {}
    this.setState({ cameraFollow });
  };
  private toggleCamera = (): void => this.setCameraFollow(!this.state.cameraFollow);
  private continueSavedGame = (): void => {
    const slot =
      this.state.saveSlots.find((item) => item.kind === "auto") ??
      this.state.saveSlots[0];
    if (slot) void this.restoreSlot(slot, false);
  };
  /** Keep stable IDs when the local seating plan changes. */
  private setPlayerCount = (count: number): void => {
    if (!Number.isInteger(count) || count < 2 || count > 4) return;
    const roster = Array.from(
      { length: count },
      (_, i) =>
        this.state.playerSetup[i] ?? {
          id: "p" + (i + 1),
          name: "玩家" + (i + 1),
          kind: "human" as const,
        },
    );
    this.setState({ playerSetup: roster });
  };
  private updatePlayer = (
    index: number,
    field: "name" | "kind",
    value: string,
  ): void => {
    const roster = this.state.playerSetup.map((p, i) => {
      if (i !== index) return p;
      const { computerStyle: _previous, ...rest } = p;
      return field === "kind"
        ? {
            ...rest,
            kind: value as "human" | "computer",
            ...(value === "computer"
              ? { computerStyle: p.computerStyle ?? "balanced" }
              : {}),
          }
        : { ...p, name: value };
    });
    this.setState({ playerSetup: roster });
  };
  private selectMap = (id: string): void => {
    const level = PLAYABLE_LEVELS.find(level => level.map.id === id);
    if (!level) return;
    const base = levelConfig(id);
    this.terminateDebugWorker();
    this.cancelCue();
    this.cpuTurnMark = "";
    this.cpuTurnActions = 0;
    this.lastCpuEvents = [];
    const fresh = createGame(20261015, {
      ...base,
      players: this.state.playerSetup,
    });
    this.setState({
      selectedMapId: id,
      roundsInput: String(base.maxRounds),
      selectedTileId: null,
      lastMotion: null,
      visualCue: null,
      financePanel: null,
      sceneEpoch: this.state.sceneEpoch + 1,
      sceneReady: false,
      debugBusy: false,
      game: fresh,
      displayGame: fresh,
      message:
        `已选择${level.name}：${level.tiles.length} 格，${level.description}。`,
    });
  };
  private acknowledgeHandoff = (): void => {
    this.setState({
      awaitingHandoff: false,
      message:
        "已轮到" +
        this.state.game.players[this.state.game.currentPlayerIndex].name +
        "操作。",
    });
  };
  startGame = (): void => {
    void this.sound.activate();
    const seed = Number(this.state.seedInput.trim());
    if (
      !/^\d{1,10}$/.test(this.state.seedInput.trim()) ||
      !Number.isSafeInteger(seed) ||
      seed > 4294967295
    ) {
      this.setState({ message: "对局种子请输入 0 至 4294967295 之间的整数。" });
      return;
    }
    const rawRounds = this.state.roundsInput.trim();
    const rounds = Number(rawRounds);
    if (
      !/^[0-9]{1,5}$/.test(rawRounds) ||
      !Number.isSafeInteger(rounds) ||
      rounds < 1 ||
      rounds > 10000
    ) {
      this.setState({ message: "最大轮数必须是 1 至 10000 的整数。" });
      return;
    }
    const roster = this.state.playerSetup.map((p) => ({
      ...p,
      name: p.name.trim(),
      ...(p.kind === "computer"
        ? { computerStyle: p.computerStyle ?? "balanced" }
        : {}),
    }));
    if (
      roster.some((p) => !p.name || p.name.length > 24) ||
      new Set(roster.map((p) => p.name)).size !== roster.length
    ) {
      this.setState({
        message: "所有玩家都必须填写不同的姓名（最多 24 字）。",
      });
      return;
    }
    let fresh: GameState;
    try {
      fresh = createGame(seed, {
        ...levelConfig(this.state.selectedMapId),
        players: roster,
        maxRounds: rounds,
        ...(this.state.endCondition==='bankruptcy'?{endCondition:'bankruptcy' as const}:{}),
        automaticLiquidation: true,
        propertyVisitOnly: true,
        stockAccount: "bank",
        bankEnabled: true,
        loanEnabled: true,
        marketEnabled: true,
        strategyEnabled: true,
        specialEnabled: this.state.specialEnabled && !!LEVELS.find(level => level.map.id === this.state.selectedMapId)?.facilityConfig,
      });
    } catch (e) {
      this.setState({
        message:
          "开局配置无效：" + (e instanceof Error ? e.message : String(e)),
      });
      return;
    }
    this.terminateDebugWorker();
    this.saveEpoch++;
    this.stopTimer();
    this.cancelCue();
    this.cpuTurnMark = "";
    this.cpuTurnActions = 0;
    this.lastCpuEvents = [];
    const result = applyAction(fresh, {
      type: "start_game",
      actorId: fresh.players[0].id,
    });
    if (!result.ok) {
      this.setState({ message: "无法开始对局，请重新开局。" });
      return;
    }
    this.setState({
      sceneEpoch: this.state.sceneEpoch + 1,
      sceneReady: false,
      debugBusy: false,
      game: result.state,
      displayGame: result.state,
      activeSeed: seed,
      cameraFollow: fresh.map.cells.length >= 60 || this.state.cameraFollow,
      selectedTileId: null,
      lastMotion: null,
      visualCue: null,
      overlay: null,
      dieValue: null,
      dieActorId: null,
      financePanel: null,
      awaitingHandoff: false,
      message: "游戏已开始！轮到" + fresh.players[0].name + "掷骰。",
    });
  };
  componentWillUnmount(): void {
    this.terminateDebugWorker();
    this.sound.dispose();
    window.removeEventListener("online", this.updateOnline);
    document.removeEventListener("visibilitychange", this.onVisibility);
    this.cancelCue();
    window.removeEventListener("offline", this.updateOnline);
    this.clearWorldTimer();
    navigator.serviceWorker?.removeEventListener(
      "controllerchange",
      this.controllerChanged,
    );
    this.stopTimer();
  }

  /** 每次状态变化只安排电脑的一步；重开后旧回调不会碰新对局。 */
  componentDidUpdate(_prevProps: object, prevState: UiState): void {
    if (
      this.state.game !== prevState.game &&
      this.state.game.status !== "setup"
    )
      this.scheduleAutosave(this.state.game);
    if (
      this.state.debugBusy ||
      this.debugWorker !== null ||
      this.state.storageBusy ||
      !this.state.sceneReady ||
      this.state.confirmText ||
      this.state.overlay ||
      this.state.cpuPaused ||
      this.state.awaitingHandoff ||
      document.hidden ||
      this.presenting
    ) {
      this.stopTimer();
      return;
    }
    const snapshot = this.state.game;
    if (
      snapshot.status !== "playing" ||
      snapshot.players[snapshot.currentPlayerIndex].kind !== "computer" ||
      this.computerTimer !== null
    )
      return;
    const scheduledDelay = cpuDelay(
      this.state.fastMode ? "fast" : "normal",
      {
        type: "roll",
        actorId: snapshot.players[snapshot.currentPlayerIndex].id,
      },
      this.lastCpuEvents,
    );
    this.computerTimer = window.setTimeout(() => {
      this.computerTimer = null;
      if (
        this.state.game !== snapshot ||
        this.state.debugBusy ||
        this.debugWorker !== null ||
        this.state.storageBusy ||
        !this.state.sceneReady ||
        this.state.cpuPaused ||
        this.state.confirmText ||
        this.state.overlay ||
        this.presenting ||
        document.hidden
      )
        return;
      const turnKey = cpuTurnKey(snapshot);
      if (turnKey !== this.cpuTurnMark) {
        this.cpuTurnMark = turnKey;
        this.cpuTurnActions = 0;
      }
      if (this.cpuTurnActions >= MAX_CPU_ACTIONS_PER_TURN) {
        this.setState({
          cpuPaused: true,
          message:
            "电脑本回合动作已达到安全上限，请检查策略与游戏状态后再继续。",
        });
        return;
      }
      const start = performance.now();
      let action: GameAction | null = null;
      let result: ReturnType<typeof applyAction> | null = null;
      try {
        action = chooseComputerAction(snapshot, { reserveCash: 200 });
        if (action) result = applyAction(snapshot, action);
      } catch (e) {
        this.setState({
          cpuPaused: true,
          message: "电脑行动异常，已自动暂停：" + String(e),
        });
        return;
      }
      const calculationMs = performance.now() - start;
      if (!action || !result) {
        this.setState({
          cpuPaused: true,
          message: "电脑没有可执行的合法行动，已暂停避免循环。",
        });
        return;
      }
      if (!result.ok) {
        this.setState({
          cpuPaused: true,
          message:
            "电脑操作失败（" + result.reason + "），请重新开局或报告缺陷。",
        });
        return;
      }
      this.cpuTurnActions++;
      this.lastCpuEvents = result.events;
      const actor = snapshot.players[snapshot.currentPlayerIndex];
      const cue = this.cueFor(snapshot, result.state, result.events);
      const moved = result.events.find((e) => e.type === "player_moved");
      const landed = result.state.players.find((p) => p.id === actor.id);
      const rent = rentCueFor(result.events),
        outcomes = outcomeSequence(result.events, result.state),
        travels = Boolean(cue?.path.length && !this.noMotion);
      this.sound.play(
        travels
          ? result.events.filter((e) => e.type === "die_rolled")
          : result.events,
      );
      this.setState(
        {
          game: result.state,
          awaitingHandoff: needsHumanHandoff(snapshot, result.state),
          displayGame: travels ? this.state.displayGame : result.state,
          visualCue: cue,
          queuedRent: travels ? rent : null,
          queuedOutcomes: travels ? outcomes : [],
          ...this.dieStateFor(result.events),
          cpuTiming: addCpuTiming(
            this.state.cpuTiming,
            calculationMs,
            scheduledDelay,
          ),
          lastMotion:
            moved && landed
              ? {
                  playerId: actor.id,
                  tileId: landed.position,
                  revision: result.state.revision,
                }
              : null,
          message: this.describe(result.events, result.state, actor.name),
        },
        () => {
          if (!travels) this.playWorldSequence(rent, outcomes);
        },
      );
    }, scheduledDelay);
  }

  private onSceneReadyChange=(sceneReady:boolean):void=>{
    if(this.state.sceneReady!==sceneReady)this.setState({sceneReady});
  };

  dispatch = async (
    type: GameAction["type"],
    tileId?: number,
    cardType?: CardKind,
    stockId?: StockId,
  ): Promise<void> => {
    if (
      this.state.rentCue ||
      this.state.outcomeCue ||
      this.state.outcomeQueue.length ||
      this.state.queuedRent ||
      this.state.queuedOutcomes.length
    ) {
      this.setState({ message: "正在播放街区结果，请稍候。" });
      return;
    }
    if (
      this.state.visualCue?.path.length &&
      this.state.visualCue.step < this.state.visualCue.path.length &&
      !this.noMotion
    ) {
      this.setState({ message: "角色正在走过街区，请稍候再操作。" });
      return;
    }
    void this.sound.activate();
    if (this.state.storageBusy || this.state.awaitingHandoff || this.state.debugBusy || this.debugWorker) return;
    const { game } = this.state;
    const actor = game.players[game.currentPlayerIndex];
    if (actor.kind === "computer") return;
    const bankAmount = /^[1-9][0-9]{0,12}$/.test(
      this.state.bankAmountInput.trim(),
    )
      ? Number(this.state.bankAmountInput.trim())
      : NaN;
    const stockAmount = /^[1-9][0-9]{0,6}$/.test(
      this.state.stockAmountInput.trim(),
    )
      ? Number(this.state.stockAmountInput.trim())
      : NaN;
    const action: GameAction =
      type === "buy_stock" || type === "sell_stock"
        ? {
            type,
            actorId: actor.id,
            stockId: stockId ?? "SEA",
            quantity: stockAmount,
          }
        : type === "upgrade_property" ||
            type === "sell_property" ||
            type === "mortgage_property" ||
            type === "release_mortgage"
          ? { type, actorId: actor.id, tileId: tileId ?? -1 }
          : type === "deposit_bank" ||
              type === "withdraw_bank" ||
              type === "borrow_loan" ||
              type === "repay_loan"
            ? { type, actorId: actor.id, amount: bankAmount }
            : type === "buy_shop_card"
              ? { type, actorId: actor.id, cardType: cardType ?? "reward" }
              : type === "use_card"
                ? {
                    type,
                    actorId: actor.id,
                    cardType: cardType ?? "reward",
                    ...(cardType === "remote"
                      ? { dieValue: Number(this.state.strategyDieInput) }
                      : {}),
                    ...(cardType === "roadblock"
                      ? {
                          tileId: Number(
                            game.tiles.some(
                              (t) =>
                                t.id ===
                                  Number(this.state.roadblockTileInput) &&
                                t.id !== 0 &&
                                t.id !== actor.position &&
                                !game.players.some(
                                  (p) => !p.bankrupt && p.position === t.id,
                                ) &&
                                !game.roadblocks?.some(
                                  (b) => b.tileId === t.id,
                                ),
                            )
                              ? this.state.roadblockTileInput
                              : (game.tiles.find(
                                  (t) =>
                                    t.id !== 0 &&
                                    t.id !== actor.position &&
                                    !game.players.some(
                                      (p) => !p.bankrupt && p.position === t.id,
                                    ) &&
                                    !game.roadblocks?.some(
                                      (b) => b.tileId === t.id,
                                    ),
                                )?.id ?? -1),
                          ),
                        }
                      : {}),
                  }
                : { type, actorId: actor.id };
    const signature = JSON.stringify(action);
    if (
      this.lastCommittedAction?.signature === signature &&
      (this.lastCommittedAction.game === game ||
        Date.now() - this.lastCommittedAction.at < 350)
    ) {
      this.setState({ message: "操作已提交，请勿重复点击。" });
      return;
    }
    const quoted =
      stockId && game.market ? quoteMarket(game.market, stockId) : 0;
    const highRisk =
      type === "mortgage_property" ||
      type === "borrow_loan" ||
      ((type === "repay_loan" ||
        type === "withdraw_bank" ||
        type === "deposit_bank") &&
        bankAmount >= 500) ||
      (type === "buy_property" &&
        (game.tiles[actor.position].price ?? 0) >= 400) ||
      (type === "upgrade_property" &&
        tileId !== undefined &&
        (quotePropertyUpgrade(game,tileId)?.cost ?? 0) >= 400) ||
      ((type === "buy_stock" || type === "sell_stock") &&
        Number.isFinite(stockAmount) &&
        (stockAmount >= 50 || quoted * stockAmount >= 300));
    if (highRisk) {
      const detail =
        type === "mortgage_property"
          ? "确认抵押地产？抵押后该地产暂不收租，贷款违约可能被银行收回。"
          : type === "borrow_loan"
            ? "确认借入 " +
              bankAmount +
              " 游戏币？贷款计息且可能触发抵押物清算。"
            : type === "buy_property"
              ? "确认购买「" +
                game.tiles[actor.position].title +
                "」？将支付 " +
                game.tiles[actor.position].price +
                " 游戏币。"
              : type === "upgrade_property"
                ? "确认升级地产？将从当前玩家现金中扣除建筑费。"
                : type === "repay_loan"
                  ? "确认偿还 " + bankAmount + " 游戏币贷款？"
                  : type === "withdraw_bank" || type === "deposit_bank"
                    ? "确认" +
                      (type === "deposit_bank" ? "存入" : "取出") +
                      " " +
                      bankAmount +
                      " 游戏币？"
                    : "确认" +
                      (type === "buy_stock" ? "买入" : "卖出") +
                      " " +
                      stockAmount +
                      " 股？股票成交后价格会波动，且需支付手续费。";
      if (!(await this.confirm(detail))) {
        this.setState({ message: "已取消操作，本局资产没有变化。" });
        return;
      }
    }
    if (this.state.game !== game || this.state.debugBusy || this.debugWorker) return;
    const result = applyAction(game, action);
    if (!result.ok) {
      const bankAction =
        type === "deposit_bank" ||
        type === "withdraw_bank" ||
        type === "borrow_loan" ||
        type === "repay_loan";
      const stockAction = type === "buy_stock" || type === "sell_stock";
      const reason =
        result.reason === "INVALID_ACTOR"
          ? "当前操作玩家已变更，请查看上方高亮玩家。"
          : stockAction
            ? result.reason === "INSUFFICIENT_FUNDS"
              ? "股票交易未执行：交易账户余额不足或持仓数量不够。"
              : "股票交易未执行：请输入有效股数，交易仅限当前玩家的结算阶段。"
            : bankAction
              ? result.reason === "INSUFFICIENT_FUNDS"
                ? "银行或借贷操作未执行：现金、存款或可借额度不足。"
                : "银行或借贷操作未执行：金额必须是有效正整数，且只能在本人结算阶段操作。"
              : result.reason === "INSUFFICIENT_FUNDS"
                ? "操作未执行：现金不足。"
                : "操作未执行：当前阶段或目标不合法，请检查所选地产、卡片目标和行动玩家。";
      this.setState({ message: reason });
      return;
    }
    this.lastCommittedAction = { game, signature, at: Date.now() };
    const cue = this.cueFor(game, result.state, result.events);
    const rent = rentCueFor(result.events),
      outcomes = outcomeSequence(result.events, result.state),
      travels = Boolean(cue?.path.length && !this.noMotion);
    this.sound.play(
      travels
        ? result.events.filter((e) => e.type === "die_rolled")
        : result.events,
    );
    const next = result.state.players[result.state.currentPlayerIndex];
    const handoff = needsHumanHandoff(game, result.state);
    const moved = result.events.find((e) => e.type === "player_moved");
    const landed = result.state.players.find((p) => p.id === actor.id);
    this.setState(
      {
        game: result.state,
        displayGame: travels ? this.state.displayGame : result.state,
        awaitingHandoff: handoff,
        visualCue: cue,
        queuedRent: travels ? rent : null,
        queuedOutcomes: travels ? outcomes : [],
        ...this.dieStateFor(result.events),
        financePanel: type === "end_turn" ? null : this.state.financePanel,
        lastMotion:
          moved && landed
            ? {
                playerId: actor.id,
                tileId: landed.position,
                revision: result.state.revision,
              }
            : null,
        message: handoff
          ? "请将设备交给 " + next.name + "；确认就位后方可继续。"
          : this.describe(result.events, result.state, actor.name),
      },
      () => {
        if (!travels) this.playWorldSequence(rent, outcomes);
      },
    );
  };

  describe = (
    events: readonly GameEvent[],
    state: GameState,
    actorName: string,
  ): string => {
    const finished = events.find((e) => e.type === "game_finished");
    if (finished) {
      const winner = state.players.find((p) => p.id === state.winnerId);
      const reason =
        finished.details?.reason === "bankruptcy"
          ? "发生破产。"
          : `达到 ${state.maxRounds} 轮上限。`;
      return `${reason}${winner ? `赢家是${winner.name}！` : "双方净资产相同，平局！"}`;
    }
    if (events.some((e) => e.type === "game_started")) return "对局已开始！";
    const stockEvent = events.find(
      (e) =>
        e.type === "stock_bought" ||
        e.type === "stock_sold" ||
        e.type === "stock_liquidated",
    );
    if (stockEvent) return this.describeEvent(stockEvent);
    const bankEvent = events.find(
      (e) => e.type === "bank_deposited" || e.type === "bank_withdrawn",
    );
    if (bankEvent)
      return bankEvent.type === "bank_deposited"
        ? `${actorName}存入银行 ${bankEvent.details?.amount} 游戏币。`
        : `${actorName}取出存款 ${bankEvent.details?.amount} 游戏币。`;
    const loanEvent = events.find((e) =>
      [
        "property_mortgaged",
        "property_released",
        "loan_borrowed",
        "loan_repaid",
        "loan_default",
        "loan_interest",
      ].includes(e.type),
    );
    if (loanEvent) return this.describeEvent(loanEvent);
    const interest = events.filter((e) => e.type === "bank_interest");
    if (interest.length)
      return `本轮银行结息 ${interest.length} 笔，总计 ${interest.reduce((sum, e) => sum + Number(e.details?.amount ?? 0), 0)} 游戏币。`;
    const upgrades = events.filter((e) => e.type === "property_upgraded");
    if(upgrades.length>1)return `${actorName}联排建设 ${upgrades.length} 户至 ${upgrades[0].details?.level} 级，共花费 ${upgrades.reduce((sum,event)=>sum+Number(event.details?.amount??0),0)} 游戏币。`;
    const upgraded = upgrades[0];
    if (upgraded)
      return `${actorName}升级了 ${upgraded.details?.tileId} 号地产至 ${upgraded.details?.level} 级，花费 ${upgraded.details?.amount} 游戏币。`;
    const used = events.find((e) => e.type === "card_used");
    if (used)
      return used.details?.cardType === "reward"
        ? `${actorName}使用奖励卡，获得 ${used.details?.amount} 游戏币。`
        : used.details?.cardType === "stride"
          ? `${actorName}使用步数卡，下次掷骰额外前进 ${used.details?.moveBonus} 格。`
          : this.describeEvent(used);
    const special = events.find(
      (e) => e.type === "event_bonus" || e.type === "event_fee",
    );
    if (special)
      return special.type === "event_bonus"
        ? `${actorName}触发幸运事件，获得 ${special.details?.amount} 游戏币。`
        : `${actorName}触发费用事件，支付 ${special.details?.amount} 游戏币（应付 ${special.details?.due}）。`;
    const bought = events.find((e) => e.type === "property_bought");
    if (bought)
      return `${actorName}花费 ${bought.details?.amount} 游戏币购买了 ${bought.details?.tileId} 号地产。现在可以结束回合。`;
    const sold = events.find((e) => e.type === "property_sold");
    if (sold)
      return `${actorName}出售了 ${sold.details?.tileId} 号地产，获得 ${sold.details?.amount} 游戏币。`;
    const rent = events.find((e) => e.type === "rent_paid");
    if (rent)
      return `${actorName}落在对手地产，${events.some((e) => e.type === "property_liquidated") ? "已自动出售地产救急，" : ""}支付 ${rent.details?.amount} 游戏币租金。${state.status === "playing" ? "现在可以结束回合。" : ""}`;
    const dice = events.find((e) => e.type === "die_rolled");
    if (dice) {
      const tile =
        state.tiles[state.players[state.currentPlayerIndex].position];
      return `${actorName}掷出 ${dice.details?.value} 点，走到了「${tile.title}」。${state.phase === "await_decision" ? `可支付 ${tile.price} 游戏币买地，或选择放弃。` : "可以结束本回合。"}`;
    }
    if (events.some((e) => e.type === "property_declined"))
      return "本次放弃购买，没有扣除游戏币。可以结束回合。";
    if (events.some((e) => e.type === "turn_ended"))
      return `轮到${state.players[state.currentPlayerIndex].name}行动，点击掷骰继续。`;
    return "操作完成。";
  };

  private cardName = (kind: unknown): string =>
    (
      ({
        reward: "奖励卡",
        stride: "步数卡",
        remote: "遥控骰子",
        roadblock: "路障",
        rent_free: "免租卡",
      }) as Record<string, string>
    )[String(kind)] ?? "卡片";

  describeEvent = (event: GameEvent): string => {
    const person =
      this.state.game.players.find((p) => p.id === event.actorId)?.name ??
      "系统";
    switch (event.type) {
      case "game_started":
        return "对局开始";
      case "die_rolled":
        return `${person}掷出 ${event.details?.value} 点`;
      case "tile_landed":
        return `${person}到达「${event.details?.title}」`;
      case "card_received":
        return `${person}在卡片站获得${this.cardName(event.details?.cardType)}`;
      case "card_used":
        return `${person}使用${this.cardName(event.details?.cardType)}${event.details?.cardType === "roadblock" ? "，放在 " + event.details?.tileId + " 号格" : event.details?.cardType === "remote" ? "，指定骰点 " + event.details?.dieValue : ""}`;
      case "roadblock_triggered":
        return `${person}碰到 ${event.details?.tileId} 号格路障，提前停下`;
      case "rent_waived":
        return `${person}免除 ${event.details?.amount} 游戏币租金`;
      case "facility_entered":
        return `${person}来到${event.details?.kind === "hospital" ? "医院" : event.details?.kind === "prison" ? "监狱" : "商店"}${event.details?.turns ? "，需跳过 " + event.details.turns + " 回合" : "，可以购买道具"}`;
      case "detention_skipped":
        return `${person}暂停行动，剩余 ${event.details?.remaining} 回合`;
      case "detention_released":
        return `${person}获准离开${event.details?.kind === "hospital" ? "医院" : "监狱"}`;
      case "shop_purchased":
        return `${person}花费 ${event.details?.amount} 游戏币购买${this.cardName(event.details?.cardType)}`;
      case "shop_left":
        return `${person}离开商店`;
      case "card_expired":
        return event.details?.cardType === "roadblock"
          ? `${person}放置在 ${event.details?.tileId} 号格的路障已过期`
          : `${person}的免租保护已到期`;
      case "event_bonus":
        return `${person}在事件格获得 ${event.details?.amount} 游戏币`;
      case "event_fee":
        return `${person}在事件格支付 ${event.details?.amount} 游戏币`;
      case "property_upgraded":
        return `${person}将 ${event.details?.tileId} 号地产升到 ${event.details?.level} 级（${event.details?.amount}）`;
      case "property_bought":
        return `${person}买下 ${event.details?.tileId} 号地产（${event.details?.amount}）`;
      case "property_sold":
        return `${person}出售 ${event.details?.tileId} 号地产，回收 ${event.details?.amount} 游戏币`;
      case "property_liquidated":
        return `${person}欠费救济，变卖 ${event.details?.tileId} 号地产收回 ${event.details?.amount} 游戏币`;
      case "property_mortgaged":
        return `${person}抵押 ${event.details?.tileId} 号地产，额度 ${event.details?.credit}`;
      case "property_released":
        return `${person}解除 ${event.details?.tileId} 号地产抵押`;
      case "loan_borrowed":
        return `${person}借入 ${event.details?.amount} 游戏币`;
      case "loan_repaid":
        return `${person}偿还贷款 ${event.details?.amount} 游戏币`;
      case "loan_interest":
        return `${person}贷款利息 ${event.details?.amount}（已付 ${event.details?.paid}）`;
      case "loan_default":
        return `${person}违约，抵押地产收回 ${event.details?.collateral} 块`;
      case "stock_bought":
        return `${person}以 ${event.details?.price} 游戏币买入 ${event.details?.stockId} ${event.details?.quantity} 股，手续费 ${event.details?.fee}`;
      case "stock_sold":
        return `${person}卖出 ${event.details?.stockId} ${event.details?.quantity} 股，手续费 ${event.details?.fee}，已实现盈亏 ${event.details?.realized}`;
      case "stock_liquidated":
        return `${person}欠租时变卖 ${event.details?.stockId} ${event.details?.quantity} 股，到账 ${event.details?.amount}`;
      case "bank_deposited":
        return `${person}存入银行 ${event.details?.amount} 游戏币`;
      case "bank_withdrawn":
        return `${person}${event.details?.reason === "rent" ? "自动取款支付租金" : "从银行取出"} ${event.details?.amount} 游戏币`;
      case "bank_interest":
        return `${person}获得本轮银行利息 ${event.details?.amount} 游戏币`;
      case "rent_paid":
        return `${person}支付租金 ${event.details?.amount}`;
      case "player_bankrupt":
        return `${person}破产`;
      case "game_finished":
        return "对局结束";
      case "property_declined":
        return `${person}放弃购买`;
      case "turn_ended":
        return `${person}结束回合`;
      case "player_moved":
        return `${person}移动到 ${event.details?.to} 号格`;
    }
  };

  private confirmResolver: ((answer: boolean) => void) | null = null;
  private confirm = (text: string): Promise<boolean> => {
    this.stopTimer();
    return new Promise((resolve) => {
      this.confirmResolver = resolve;
      this.setState({ confirmText: text });
    });
  };
  private resolveConfirmation = (answer: boolean): void => {
    const resolve = this.confirmResolver;
    this.confirmResolver = null;
    this.setState({ confirmText: null }, () => resolve?.(answer));
  };
  private closeOverlay = (): void => {
    if (this.debugWorker) this.cancelDebugSimulation();
    this.setState({ overlay: null, financePanel: null });
  };
  private openOverlay = (overlay: NonNullable<UiState["overlay"]>): void => {
    if (this.debugWorker) this.cancelDebugSimulation();
    this.stopTimer();
    if (overlay === "debug") {
      this.skipPresentation();
      this.setState({ debugMessage: "" });
    }
    this.setState({
      overlay,
      financePanel: ["property", "bank", "loan", "stock"].includes(overlay)
        ? (overlay as UiState["financePanel"])
        : null,
    });
  };
  private get presenting(): boolean {
    return Boolean(
      this.state.visualCue?.path.length ||
        this.state.queuedRent ||
        this.state.queuedOutcomes.length ||
        this.state.rentCue ||
        this.state.outcomeCue ||
        this.state.outcomeQueue.length,
    );
  }
  private renderSettings(): React.JSX.Element {
    return (
      <div className="settings-list">
        <label className="setting-line">
          <span>
            <strong>音效</strong>
            <small>掷骰、买地与回合提示音</small>
          </span>
          <input
            type="checkbox"
            aria-label="开启音效"
            checked={this.sound.isEnabled}
            onChange={() => {
              void this.sound.setEnabled(!this.sound.isEnabled);
              this.setState({});
            }}
          />
        </label>
        <label className="setting-line">
          <span>音效音量</span>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            aria-label="音效音量"
            value={Math.round(this.sound.level * 100)}
            onChange={(e) => {
              this.sound.setVolume(Number(e.target.value) / 100);
              this.setState({});
            }}
          />
        </label>
        <label className="setting-line">
          <span>
            <strong>减少动态效果</strong>
            <small>立即展示行走与交易结果</small>
          </span>
          <input
            type="checkbox"
            aria-label="减少动态效果"
            checked={this.state.motionOff}
            onChange={this.toggleMotion}
          />
        </label>
        <label className="setting-line">
          <span>
            <strong>跟随当前玩家</strong>
            <small>关闭后保持整张地图的全景</small>
          </span>
          <input
            type="checkbox"
            aria-label="跟随当前玩家"
            checked={this.state.cameraFollow}
            onChange={this.toggleCamera}
          />
        </label>
        <p className="panel-note">偏好只保存在本机，不改变游戏存档。</p>
        <details>
          <summary>版本与离线状态</summary>
          <p>ReactMono · 静态本机游戏</p>
          <p>
            {this.state.offline ? "当前离线，可以继续本机游玩。" : "当前在线。"}
            {this.state.pwaMessage}
          </p>
          {this.state.pwaUpdate && (
            <button onClick={() => void this.applyPwaUpdate()}>
              保存并更新版本
            </button>
          )}
        </details>
      </div>
    );
  }
  private renderSaves(): React.JSX.Element {
    const { game, saveSlots, storageBusy, importPreview } = this.state;
    return (
      <section className="saves-card">
        <p className="panel-note">
          存档只保存在这个浏览器中。清除站点数据前，请导出 JSON 备份。
        </p>
        <p className="save-message" role="status">
          {this.state.saveStatus}
        </p>
        {game.status !== "setup" && (
          <button
            className="primary-btn"
            disabled={storageBusy || this.manualSaveBusy}
            onClick={() => void this.newManualSlot()}
          >
            创建手动存档
          </button>
        )}
        {!saveSlots.length && (
          <div className="empty-state">
            这里还没有存档。开始一局后会自动保存。
          </div>
        )}
        <ul className="save-list">
          {saveSlots.map((slot) => (
            <li key={slot.id}>
              <div>
                <strong>{slot.name}</strong>
                <small>
                  {slot.kind === "auto" ? "自动存档" : "手动存档"} ·{" "}
                  {new Date(slot.updatedAt).toLocaleString("zh-CN")}
                </small>
              </div>
              <div className="save-actions">
                <button
                  disabled={storageBusy}
                  onClick={() =>
                    void this.restoreSlot(slot, game.status !== "setup")
                  }
                >
                  读取
                </button>
                <button
                  disabled={storageBusy}
                  onClick={() => void this.exportSlot(slot)}
                >
                  导出
                </button>
                {slot.kind === "manual" && game.status !== "setup" && (
                  <button
                    disabled={storageBusy}
                    onClick={() => void this.overwriteSlot(slot)}
                  >
                    覆盖
                  </button>
                )}
                <button
                  className="danger-text"
                  disabled={storageBusy}
                  onClick={() => void this.removeSlot(slot)}
                >
                  删除
                </button>
              </div>
            </li>
          ))}
        </ul>
        <label className="import-label">
          导入本机备份
          <input
            type="file"
            accept=".json,application/json"
            aria-label="导入 JSON 存档文件"
            onChange={(e) => void this.selectImport(e)}
          />
        </label>
        {importPreview && (
          <section className="import-preview" aria-label="存档导入预览">
            <strong>导入预览 · 第 {importPreview.game.round} 轮</strong>
            <p>
              {importPreview.game.players
                .map((p) => p.name + "：现金 " + p.cash)
                .join(" · ")}
              ；{importPreview.game.tiles.filter((t) => t.ownerId).length}{" "}
              块已有地产。
            </p>
            <label>
              存档名称
              <input
                aria-label="导入存档名称"
                value={this.state.importName}
                maxLength={60}
                onChange={(e) => this.setState({ importName: e.target.value })}
              />
            </label>
            <div className="button-row">
              {saveSlots.some(
                (s) => s.name === this.state.importName.trim(),
              ) ? (
                <>
                  <button onClick={() => void this.applyImport("overwrite")}>
                    覆盖同名存档
                  </button>
                  <button onClick={() => void this.applyImport("new")}>
                    另存为副本
                  </button>
                </>
              ) : (
                <button
                  className="primary-btn"
                  onClick={() => void this.applyImport("new")}
                >
                  确认导入存档
                </button>
              )}
              <button
                onClick={() =>
                  this.setState({ importPreview: null, importName: "" })
                }
              >
                取消导入
              </button>
            </div>
          </section>
        )}
      </section>
    );
  }
  private renderHelp(): React.JSX.Element {
    return (
      <div className="help-content">
        <p className="lead">掷一次骰子，做一次生意。</p>
        <ol>
          <li>
            <strong>掷骰出发</strong>
            <p>轮到你时，先使用手牌（如果有），再沿环线掷骰前进。</p>
          </li>
          <li>
            <strong>经营地产</strong>
            <p>
              到达无主地产可购买或放弃。以后再次到访自己的土地，可以建房、升级；每次到访限一次操作。停在对手地产会自动支付租金。
            </p>
            {this.state.game.map.id==='lime-garden-30'&&<p>{this.state.game.terraceRulesVersion===1
              ? '青柠游园：同街区连续的同主土地组成联排。到访其中任意一格，可一次补建整排最低等级房屋，费用合计扣除；对手到访支付整排当前通行费。空地也参与，抵押、出售或他人土地会断开联排。'
              : '本局为旧版单地块规则。新建青柠游园对局可体验街区联排建设与合计通行费。'}</p>}
          </li>
          <li>
            <strong>安排资产</strong>
            <p>
              处理完地块后，可在银行存取款、抵押借贷、交易股票。现金用于地产与建设，银行存款用于新对局的股票交易。
            </p>
          </li>
          <li>
            <strong>结束回合</strong>
            <p>
              电脑自动行动；本机多人需交接设备。默认以破产决胜，最后一位未破产玩家获胜；可在对局设置中改为限轮后比较净资产。
            </p>
          </li>
        </ol>
        <p className="panel-note">
          净资产＝现金＋存款＋地产计价＋股票市值－贷款。存档保存在本机，可手动导出和导入。
        </p>
      </div>
    );
  }
  private renderFinance(): React.JSX.Element {
    const game = this.state.game,
      current = game.players[game.currentPlayerIndex],
      panel = this.state.overlay;
    const canTrade =
      game.status === "playing" &&
      current.kind === "human" &&
      !this.state.awaitingHandoff &&
      !this.presenting &&
      game.phase === "await_end_turn";
    const amount = Number(this.state.bankAmountInput),
      amountValid = /^[1-9][0-9]{0,12}$/.test(this.state.bankAmountInput);
    const quantity = Number(this.state.stockAmountInput),
      quantityValid = /^[1-9][0-9]{0,6}$/.test(this.state.stockAmountInput);
    return (
      <div className="finance-workspace">
        <nav className="finance-tabs" aria-label="交易操作快捷入口">
          {(
            [
              { id: "property", label: "地产" },
              ...(game.bank ? [{ id: "bank", label: "银行" }] : []),
              ...(game.loan ? [{ id: "loan", label: "抵押借贷" }] : []),
              ...(game.market ? [{ id: "stock", label: "股票" }] : []),
            ] as const
          ).map((link) => (
            <button
              key={link.id}
              aria-expanded={panel === link.id}
              className={panel === link.id ? "is-selected" : ""}
              onClick={() =>
                this.openOverlay(link.id as NonNullable<UiState["overlay"]>)
              }
            >
              {link.label}
            </button>
          ))}
        </nav>
        <div className="account-summary">
          <span>
            现金 <b>{current.cash.toLocaleString("zh-CN")}</b>
          </span>
          <span>
            银行存款 <b>{(current.bankBalance ?? 0).toLocaleString("zh-CN")}</b>
          </span>
          <span>
            贷款 <b>{(current.loanBalance ?? 0).toLocaleString("zh-CN")}</b>
          </span>
        </div>
        {!canTrade && (
          <p className="panel-note">
            当前可查看资产；交易在本人处理完到访地块后开放。
          </p>
        )}
        {canTrade && (
          <p className="panel-note">
            当前可交易。办理完成后关闭窗口，继续本回合。
          </p>
        )}
        {(panel === "bank" || panel === "loan") && (
          <label className="amount-field">
            {panel === "bank" ? "银行交易金额" : "借还款金额"}
            <input
              id="bank-amount"
              aria-label="银行交易金额"
              inputMode="numeric"
              value={this.state.bankAmountInput}
              onChange={(e) =>
                this.setState({ bankAmountInput: e.target.value })
              }
            />
          </label>
        )}
        {panel === "bank" && game.bank && (
          <section id="bank-actions" className="bank-actions">
            <h3>银行存取</h3>
            <p>
              每轮结息 {game.bank.interestBps / 100}%。欠租时会优先自动取款。
            </p>
            <div className="transaction-preview">
              {amountValid ? (
                <>
                  存入后：现金 {(current.cash - amount).toLocaleString("zh-CN")}{" "}
                  · 存款{" "}
                  {((current.bankBalance ?? 0) + amount).toLocaleString(
                    "zh-CN",
                  )}
                </>
              ) : (
                "请输入正整数金额。"
              )}
            </div>
            <div className="button-row">
              <button
                className="primary-btn"
                disabled={!canTrade || !amountValid || amount > current.cash}
                onClick={() => this.dispatch("deposit_bank")}
              >
                存入银行
              </button>
              <button
                disabled={
                  !canTrade ||
                  !amountValid ||
                  amount > (current.bankBalance ?? 0)
                }
                onClick={() => this.dispatch("withdraw_bank")}
              >
                从银行取款
              </button>
            </div>
          </section>
        )}
        {panel === "property" && (
          <section id="finance-property" className="finance-pane">
            <h3>地产管理 · {current.name}</h3>
            {!game.tiles.some((t) => t.ownerId === current.id) && (
              <p className="empty-state">
                尚未持有地产。到达无主土地时可以购买。
              </p>
            )}
            {game.tiles
              .filter((t) => t.ownerId === current.id)
              .map((tile) => {
                const level = tile.level ?? 0,
                  quote = quotePropertyUpgrade(game,tile.id),
                  cost = quote?.cost ?? Infinity,
                  visit = propertyVisitAvailable(game, current, tile.id);
                return (
                  <article className="property-entry" key={tile.id}>
                    <div>
                      <strong>{tile.title}</strong>
                      <small>
                        {tile.id + 1} 号格 ·{" "}
                        {level === 0
                          ? "土地"
                          : level === 1
                            ? "住宅"
                            : "高级住宅"}{" "}
                        ·{" "}
                        {tile.mortgaged
                          ? "已抵押，暂停收租"
                          : "通行费 " + propertyRent(game,tile.id)}
                        {game.terraceRulesVersion===1 && ` · ${propertyBlock(game,tile.id)?.title} · ${propertyRun(game,tile.id).length} 块连地`}
                      </small>
                    </div>
                    <div className="button-row">
                      {quote && !tile.mortgaged && (
                        <button
                          disabled={!canTrade || !visit || current.cash < cost}
                          onClick={() =>
                            this.dispatch("upgrade_property", tile.id)
                          }
                        >
                          {visit
                            ? (quote.tileIds.length>1 ? `联排建设 ${quote.upgrades.length} 户` : level === 0 ? "建造住宅" : "升级房屋") +
                              " · " +
                              cost
                            : "再次到访后可建设"}
                        </button>
                      )}
                      <button
                        disabled={!canTrade || !!tile.mortgaged}
                        onClick={async () => {
                          if (
                            await this.confirm(
                              "确认出售「" +
                                tile.title +
                                "」？回收 " +
                                resaleValue(tile, game.resaleRules) +
                                " 游戏币。",
                            )
                          )
                            this.dispatch("sell_property", tile.id);
                        }}
                      >
                        出售 · {resaleValue(tile, game.resaleRules)}
                      </button>
                    </div>
                  </article>
                );
              })}
          </section>
        )}
        {panel === "loan" && game.loan && (
          <section id="loan-actions" className="bank-actions">
            <h3>抵押与贷款</h3>
            <p>
              每轮利率 {game.loan.interestBps / 100}
              %。抵押地产暂停收租、建设及出售；违约可能被收回。
            </p>
            <div className="property-list">
              {game.tiles
                .filter((t) => t.ownerId === current.id)
                .map((tile) => (
                  <div className="property-entry" key={tile.id}>
                    <strong>{tile.title}</strong>
                    <button
                      disabled={
                        !canTrade ||
                        (tile.mortgaged === true &&
                          (current.loanBalance ?? 0) >
                            loanLimit(game, current.id, tile.id))
                      }
                      onClick={() =>
                        this.dispatch(
                          tile.mortgaged
                            ? "release_mortgage"
                            : "mortgage_property",
                          tile.id,
                        )
                      }
                    >
                      {tile.mortgaged ? "解除抵押" : "抵押地产"}
                    </button>
                  </div>
                ))}
            </div>
            <p>
              当前抵押额度 {loanLimit(game, current.id)} · 可借{" "}
              {Math.max(
                0,
                loanLimit(game, current.id) - (current.loanBalance ?? 0),
              )}{" "}
              游戏币
            </p>
            <div className="button-row">
              <button
                disabled={
                  !canTrade ||
                  !amountValid ||
                  amount >
                    loanLimit(game, current.id) - (current.loanBalance ?? 0)
                }
                onClick={() => this.dispatch("borrow_loan")}
              >
                借入贷款
              </button>
              <button
                disabled={
                  !canTrade ||
                  !amountValid ||
                  amount > Math.min(current.cash, current.loanBalance ?? 0)
                }
                onClick={() => this.dispatch("repay_loan")}
              >
                偿还贷款
              </button>
            </div>
          </section>
        )}
        {panel === "stock" && game.market && (
          <section id="stock-actions" className="stock-actions">
            <p>
              {game.stockAccount === "bank" ? "使用银行存款" : "此存档使用现金"}
              交易 · 手续费 0.5%，最低 1 币 · 每轮更新行情
            </p>
            <label className="amount-field">
              交易股数
              <input
                id="stock-amount"
                aria-label="股票交易数量"
                inputMode="numeric"
                value={this.state.stockAmountInput}
                onChange={(e) =>
                  this.setState({ stockAmountInput: e.target.value })
                }
              />
            </label>
            {STOCKS.map((stock) => {
              const price = quoteMarket(game.market!, stock.id),
                held = current.holdings?.[stock.id],
                total = price * quantity,
                fee = Math.max(1, Math.ceil(total * 0.005)),
                funds =
                  game.stockAccount === "bank"
                    ? (current.bankBalance ?? 0)
                    : current.cash;
              return (
                <article className="stock-entry" key={stock.id}>
                  <div className="stock-heading">
                    <strong>{stock.name}</strong>
                    <span>
                      {price} <small>币 / 股</small>
                    </span>
                  </div>
                  <p>
                    持有 {held?.quantity ?? 0} 股 · 成本 {held?.costBasis ?? 0}{" "}
                    · 市值 {(held?.quantity ?? 0) * price}
                  </p>
                  <p className="transaction-preview">
                    {quantityValid
                      ? `买入支出 ${total + fee}（含手续费 ${fee}） · 卖出到账 ${total - fee}`
                      : "请输入正整数股数。"}
                  </p>
                  <div className="button-row">
                    <button
                      disabled={
                        !canTrade || !quantityValid || total + fee > funds
                      }
                      onClick={() =>
                        this.dispatch(
                          "buy_stock",
                          undefined,
                          undefined,
                          stock.id,
                        )
                      }
                    >
                      买入 {stock.name}
                    </button>
                    <button
                      disabled={
                        !canTrade ||
                        !quantityValid ||
                        quantity > (held?.quantity ?? 0)
                      }
                      onClick={() =>
                        this.dispatch(
                          "sell_stock",
                          undefined,
                          undefined,
                          stock.id,
                        )
                      }
                    >
                      卖出 {stock.name}
                    </button>
                  </div>
                </article>
              );
            })}
          </section>
        )}
        <p className="panel-feedback" role="status">
          {this.state.message}
        </p>
      </div>
    );
  }
  private renderCards(): React.JSX.Element {
    const game = this.state.game,
      current = game.players[game.currentPlayerIndex];
    const legal =
      game.status === "playing" &&
      current.kind === "human" &&
      game.phase === "await_roll" &&
      !current.detention &&
      !this.presenting &&
      !this.state.awaitingHandoff;
    const available = game.tiles.filter(
      (t) =>
        t.id !== 0 &&
        t.id !== current.position &&
        !game.players.some((p) => !p.bankrupt && p.position === t.id) &&
        !game.roadblocks?.some((b) => b.tileId === t.id),
    );
    const kinds = (
      ["reward", "stride", "remote", "roadblock", "rent_free"] as const
    ).filter((k) => (current.cards?.[k] ?? 0) > 0);
    return (
      <div className="hand-cards">
        <p className="panel-note">
          {legal
            ? "掷骰前可使用手牌。"
            : "当前仅可查看；手牌在本人掷骰前使用。"}{" "}
          持有 {kinds.reduce((sum, k) => sum + (current.cards?.[k] ?? 0), 0)} /{" "}
          {game.cardRules?.maxHand ?? 3} 张
        </p>
        {!kinds.length && (
          <div className="empty-state">
            手里暂时没有卡片。途经卡片站或到访商店可以获得。
          </div>
        )}
        {kinds.map((k) => (
          <article className="hand-card" key={k}>
            <strong>
              {this.cardName(k)} <span>×{current.cards?.[k]}</span>
            </strong>
            <p>
              {k === "reward"
                ? `获得 ${game.cardRules?.rewardCash ?? 80} 现金。`
                : k === "stride"
                  ? `下次前进额外增加 ${game.cardRules?.moveBonus ?? 2} 格。`
                  : k === "remote"
                    ? "指定下一次骰点。"
                    : k === "roadblock"
                      ? "让经过的玩家提前停下，最多保留两轮。"
                      : "免除下一次落地租金。"}
            </p>
            {k === "remote" && (
              <label>
                骰点
                <select
                  aria-label="遥控骰点"
                  value={this.state.strategyDieInput}
                  onChange={(e) =>
                    this.setState({ strategyDieInput: e.target.value })
                  }
                >
                  {[1, 2, 3, 4, 5, 6].map((n) => (
                    <option key={n} value={n}>
                      {n} 点
                    </option>
                  ))}
                </select>
              </label>
            )}
            {k === "roadblock" && (
              <label>
                放置位置
                <select
                  aria-label="路障目标格"
                  value={
                    available.some(
                      (t) => String(t.id) === this.state.roadblockTileInput,
                    )
                      ? this.state.roadblockTileInput
                      : String(available[0]?.id ?? "")
                  }
                  onChange={(e) =>
                    this.setState({ roadblockTileInput: e.target.value })
                  }
                >
                  {available.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.id + 1} · {t.title}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <button
              disabled={
                !legal ||
                (k === "remote" && !!game.pendingDie) ||
                (k === "stride" && !!game.pendingMoveBonus) ||
                (k === "rent_free" && !!game.pendingRentWaiver) ||
                (k === "roadblock" && !available.length)
              }
              onClick={() => this.dispatch("use_card", undefined, k)}
            >
              {k === "roadblock" ? "放置路障" : "使用" + this.cardName(k)}
            </button>
          </article>
        ))}
        <p className="panel-feedback" role="status">
          {this.state.message}
        </p>
      </div>
    );
  }
  private renderAssets(): React.JSX.Element {
    const game = this.state.game;
    return (
      <div className="asset-grid">
        {game.players.map((p, i) => (
          <article className="asset-player" key={p.id} data-player-id={p.id}>
            <div className="asset-identity">
              <SeatAvatar seat={i} />
              <div>
                <strong>{p.name}</strong>
                <small>
                  {p.bankrupt
                    ? "已破产"
                    : p.kind === "computer"
                      ? "电脑玩家"
                      : "本机玩家"}
                </small>
              </div>
            </div>
            <dl className="asset-metrics">
              {[
                ["现金", p.cash],
                ["银行存款", p.bankBalance ?? 0],
                ["地产", game.tiles.filter((t) => t.ownerId === p.id).length],
                [
                  "股票市值",
                  game.market
                    ? STOCKS.reduce(
                        (sum, s) =>
                          sum +
                          (p.holdings?.[s.id]?.quantity ?? 0) *
                            quoteMarket(game.market!, s.id),
                        0,
                      )
                    : 0,
                ],
                ["贷款", p.loanBalance ?? 0],
                ["净资产", netWorth(game, p.id)],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value.toLocaleString("zh-CN")}</dd>
                </div>
              ))}
            </dl>
            {p.detention && (
              <p>
                停留{p.detention.kind === "hospital" ? "医院" : "监狱"} · 剩余{" "}
                {p.detention.remaining} 回合
              </p>
            )}
          </article>
        ))}
      </div>
    );
  }
  private renderOverlay(): React.JSX.Element | null {
    if (this.state.confirmText)
      return (
        <Modal title="确认操作" onClose={() => this.resolveConfirmation(false)}>
          <p className="confirmation-copy">{this.state.confirmText}</p>
          <div className="button-row">
            <button onClick={() => this.resolveConfirmation(false)}>
              取消
            </button>
            <button
              className="primary-btn"
              onClick={() => this.resolveConfirmation(true)}
            >
              确认操作
            </button>
          </div>
        </Modal>
      );
    const overlay = this.state.overlay;
    if (!overlay) return null;
    const game = this.state.game;
    const names = {
      results: "对局结算",
      debug: "调试工具",
      menu: "游戏菜单",
      assets: "玩家资产",
      bank: "银行",
      loan: "抵押借贷",
      stock: "股票交易所",
      property: "地产管理",
      cards: "我的手牌",
      saves: "本机存档",
      help: "玩法说明",
      settings: "游戏设置",
      tiles: "地图与地块",
      events: "小镇纪事",
    };
    return (
      <Modal title={names[overlay]} onClose={this.closeOverlay}>
        {overlay === "menu" && (
          <nav className="menu-grid" aria-label="游戏菜单">
            {game.status === "finished" && (
              <button onClick={() => this.openOverlay("results")}><strong>对局结算</strong><small>最终排名与结束原因</small><span>→</span></button>
            )}
            {(
              [
                { id: "assets", label: "玩家资产", sub: "现金、地产与净资产" },
                { id: "saves", label: "存档", sub: "保存、读取与文件备份" },
                { id: "settings", label: "设置", sub: "音效、镜头与动态效果" },
                { id: "help", label: "玩法说明", sub: "回合、交易与胜负规则" },
                { id: "tiles", label: "地图与地块", sub: "查看每一块土地" },
                { id: "events", label: "事件", sub: "回顾最近的行动" },
                { id: "debug", label: "调试工具", sub: "设置现金、后台批量推进" },
              ] as const
            ).map((item) => (
              <button key={item.id} onClick={() => this.openOverlay(item.id)}>
                <strong>{item.label}</strong>
                <small>{item.sub}</small>
                <span>→</span>
              </button>
            ))}
            <button
              className="menu-return"
              onClick={async () => {
                if (
                  await this.confirm("返回标题页？本局进度保留在自动存档中。")
                )
                  this.reset();
              }}
            >
              <strong>返回标题</strong>
              <small>保留自动存档</small>
              <span>↗</span>
            </button>
          </nav>
        )}
        {overlay === "results" && game.status === "finished" && <PostgameRanking game={game}/>}
        {overlay === "debug" && <DebugTools game={game} busy={this.state.debugBusy} message={this.state.debugMessage} onCash={this.setPlayerDebugCash} onSimulate={this.simulateDebugGame} onCancel={this.cancelDebugSimulation} />}
        {overlay === "assets" && this.renderAssets()}
        {(["bank", "loan", "stock", "property"] as string[]).includes(
          overlay,
        ) && this.renderFinance()}
        {overlay === "cards" && this.renderCards()}
        {overlay === "saves" && this.renderSaves()}
        {overlay === "help" && this.renderHelp()}
        {overlay === "settings" && this.renderSettings()}
        {overlay === "events" && (
          <ol className="event-list">
            {game.events
              .filter((e) => e.type !== "player_moved")
              .slice(-40)
              .reverse()
              .map((e, i) => (
                <li key={i}>{this.describeEvent(e)}</li>
              ))}
          </ol>
        )}
        {overlay === "tiles" && (
          <div className="tile-semantic-list">
            {game.tiles.map((tile) => (
              <button
                key={tile.id}
                className="map-tile-entry"
                data-tile-id={tile.id}
                data-owner-id={tile.ownerId ?? ""}
                data-level={tile.level ?? 0}
                aria-pressed={this.state.selectedTileId === tile.id}
                onClick={() => this.setState({ selectedTileId: tile.id })}
              >
                <b>{tile.id + 1}</b>
                <strong>{tile.title}</strong>
                <small>
                  {tile.kind === "property"
                    ? `地价 ${tile.price} · ${tile.ownerId ? game.players.find((p) => p.id === tile.ownerId)?.name + " · " + (tile.level ?? 0) + " 级" : "尚无地主"}`
                    : tile.facility
                      ? { hospital: "医院", prison: "监狱", shop: "商店" }[
                          tile.facility
                        ]
                      : tile.cardStation
                        ? "卡片站"
                        : tile.eventBonus !== undefined
                          ? "机会事件"
                          : "公共地块"}
                </small>
              </button>
            ))}
          </div>
        )}
      </Modal>
    );
  }
  private renderSetup(): React.JSX.Element {
    const screen = this.state.setupScreen;
    const continueSlot =
      this.state.saveSlots.find((s) => s.kind === "auto") ??
      this.state.saveSlots[0];
    return (
      <main className="title-shell" data-setup-screen={screen}>
        <header className="title-header">
          <span className="brand-mark">富</span>
          <strong>大富翁</strong>
          <span>晴湾小镇</span>
        </header>
        {screen === "title" ? (
          <>
            <div className="title-art">
              <div className="title-orbit" />
              <TownIllustration />
              <span className="art-caption">一座小镇，无数种可能。</span>
            </div>
            <section className="title-menu" aria-labelledby="game-title">
              <p className="eyebrow">欢迎来到晴湾小镇</p>
              <h1 id="game-title" aria-label="大富翁">
                大富翁<span>把好运，变成好生意。</span>
              </h1>
              <p className="title-description">
                掷骰出发，买下一块土地。
                <br />
                和朋友或电脑，一起经营属于你的小镇。
              </p>
              <div className="title-menu-buttons">
                {continueSlot ? (
                  <>
                    <button
                      className="title-primary"
                      disabled={this.state.storageBusy}
                      onClick={this.continueSavedGame}
                    >
                      继续游戏 <span>→</span>
                    </button>
                    <p className="title-save-summary">
                      {continueSlot.name} ·{" "}
                      {new Date(continueSlot.updatedAt).toLocaleString("zh-CN")}
                    </p>
                    <button
                      onClick={() =>
                        this.setState({ setupScreen: "new-game", message: "" })
                      }
                    >
                      新游戏
                    </button>
                  </>
                ) : (
                  <button
                    className="title-primary"
                    onClick={() =>
                      this.setState({ setupScreen: "new-game", message: "" })
                    }
                  >
                    开始游戏 <span>→</span>
                  </button>
                )}
                <button onClick={() => this.openOverlay("saves")}>
                  读取存档
                </button>
                <div className="title-minor-links">
                  <button onClick={() => this.openOverlay("settings")}>
                    设置
                  </button>
                  <button onClick={() => this.openOverlay("help")}>
                    玩法说明
                  </button>
                </div>
              </div>
              <p className="title-local-note">2～4 人 · 本机轮流 · 无需账号</p>
            </section>
          </>
        ) : (
          <section className="new-game-card" aria-labelledby="setup-title">
            <div className="setup-heading">
              <button
                className="setup-back"
                onClick={() =>
                  this.setState({ setupScreen: "title", message: "" })
                }
              >
                ← 返回
              </button>
              <div>
                <p className="eyebrow">新局准备</p>
                <h1 id="setup-title">今天，谁是小镇首富？</h1>
              </div>
            </div>
            <div className="setup-scroll">
              <div
                className="setup-map-choice"
                role="group"
                aria-label="选择地图"
              >
                {PLAYABLE_LEVELS.map((m) => (
                  <button
                    key={m.map.id}
                    data-map-id={m.map.id}
                    className={
                      this.state.selectedMapId === m.map.id ? "selected" : ""
                    }
                    aria-pressed={this.state.selectedMapId === m.map.id}
                    onClick={() => this.selectMap(m.map.id)}
                  >
                    <div className="map-card-art">
                      <LevelPreview map={m.map}/>
                    </div>
                    <div>
                      <strong>{m.name}</strong>
                      <small>{m.description}</small>
                    </div>
                    <span className="map-check">
                      {this.state.selectedMapId === m.map.id ? "✓" : "○"}
                    </span>
                  </button>
                ))}
              </div>
              <div className="setup-seat-row">
                <h2>安排玩家</h2>
                <span>在这台设备轮流操作</span>
                <select
                  aria-label="玩家人数"
                  value={this.state.playerSetup.length}
                  onChange={(e) => this.setPlayerCount(Number(e.target.value))}
                >
                  {[2, 3, 4].map((n) => (
                    <option key={n} value={n}>
                      {n} 位玩家
                    </option>
                  ))}
                </select>
              </div>
              <div className="setup-roster">
                {this.state.playerSetup.map((p, i) => (
                  <article
                    className="setup-player"
                    key={p.id}
                    data-player-id={p.id}
                  >
                    <div className="seat-heading">
                      <SeatAvatar seat={i} />
                      <span>席位 {i + 1}</span>
                    </div>
                    <label>
                      玩家姓名
                      <input
                        aria-label={`第 ${i + 1} 位玩家姓名`}
                        maxLength={24}
                        value={p.name}
                        onChange={(e) =>
                          this.updatePlayer(i, "name", e.target.value)
                        }
                      />
                    </label>
                    <label>
                      操作方式
                      <select
                        aria-label={`第 ${i + 1} 位玩家类型`}
                        value={p.kind ?? "human"}
                        onChange={(e) =>
                          this.updatePlayer(i, "kind", e.target.value)
                        }
                      >
                        <option value="human">真人 · 本机轮流</option>
                        <option value="computer">电脑</option>
                      </select>
                    </label>
                    {p.kind === "computer" && (
                      <label>
                        电脑策略
                        <select
                          aria-label={`第 ${i + 1} 位电脑策略`}
                          value={p.computerStyle ?? "balanced"}
                          onChange={(e) =>
                            this.setState({
                              playerSetup: this.state.playerSetup.map(
                                (item, j) =>
                                  j === i
                                    ? {
                                        ...item,
                                        computerStyle: e.target
                                          .value as (typeof COMPUTER_STYLES)[number],
                                      }
                                    : item,
                              ),
                            })
                          }
                        >
                          {COMPUTER_STYLES.map((s) => (
                            <option key={s} value={s}>
                              {COMPUTER_STYLE_NAMES[s]}
                            </option>
                          ))}
                        </select>
                      </label>
                    )}
                  </article>
                ))}
              </div>
              <details className="setup-more">
                <summary>
                  对局设置{" "}
                  <span>
                    {this.state.endCondition==='bankruptcy'?'破产决胜':this.state.roundsInput+' 轮结算'} ·{" "}
                    {this.state.specialEnabled ? "含特殊设施" : "标准设施"} ·
                    更多设置
                  </span>
                </summary>
                <div className="setup-setting-grid">
                  <label>对局结束方式
                    <select aria-label="对局结束方式" value={this.state.endCondition} onChange={e=>this.setState({endCondition:e.target.value as 'bankruptcy'|'round_limit'})}>
                      <option value="bankruptcy">破产决胜 · 不限轮数</option>
                      <option value="round_limit">限轮结算 · 比较净资产</option>
                    </select>
                  </label>
                  <label>
                    限轮模式最多轮数
                    <input
                      aria-label="最多轮数"
                      inputMode="numeric"
                      value={this.state.roundsInput}
                      maxLength={5}
                      onChange={(e) =>
                        this.setState({ roundsInput: e.target.value, endCondition: 'round_limit' })
                      }
                    />
                  </label>
                  <label>
                    对局种子
                    <input
                      aria-label="对局种子"
                      inputMode="numeric"
                      value={this.state.seedInput}
                      maxLength={10}
                      onChange={(e) =>
                        this.setState({ seedInput: e.target.value })
                      }
                    />
                  </label>
                  <label className="check-field">
                    <input
                      type="checkbox"
                      aria-label="启用医院、监狱与商店"
                      checked={this.state.specialEnabled && !!LEVELS.find(level => level.map.id === this.state.selectedMapId)?.facilityConfig}
                      disabled={!LEVELS.find(level => level.map.id === this.state.selectedMapId)?.facilityConfig}
                      onChange={(e) =>
                        this.setState({ specialEnabled: e.target.checked })
                      }
                    />
                    医院、监狱与商店
                  </label>
                  <label className="check-field">
                    <input
                      type="checkbox"
                      aria-label="快速模式"
                      checked={this.state.fastMode}
                      onChange={(e) =>
                        this.setState({ fastMode: e.target.checked })
                      }
                    />
                    加快电脑行动
                  </label>
                </div>
              </details>
              <p className="setup-error" role="status">
                {this.state.message}
              </p>
            </div>
            <footer className="setup-footer">
              <span>每人 {levelConfig(this.state.selectedMapId).initialCash.toLocaleString('zh-CN')} 现金 · {this.state.endCondition==='bankruptcy'?'破产决胜':`最多 ${this.state.roundsInput} 轮`}</span>
              <button
                className="title-primary"
                aria-label="开始游戏"
                onClick={this.startGame}
              >
                开始游戏 <span>→</span>
              </button>
            </footer>
          </section>
        )}
        <footer className="title-footer">
          <span>纯本地游玩 · 进度自动保存</span>
          <span>晴湾小镇 · 大富翁</span>
        </footer>
        {this.renderOverlay()}
      </main>
    );
  }
  render(): React.JSX.Element {
    const game = this.state.displayGame;
    if (game.status === "setup") return this.renderSetup();
    const current = game.players[game.currentPlayerIndex],
      target = game.tiles[current.position],
      busy = this.presenting;
    const human =
      current.kind === "human" &&
      !this.state.awaitingHandoff &&
      !busy &&
      game.status === "playing";
    const construction = quotePropertyUpgrade(game,target.id);
    const visit =
      game.phase === "await_end_turn" &&
      target.ownerId === current.id &&
      !target.mortgaged &&
      construction !== null &&
      propertyVisitAvailable(game, current, target.id);
    const cost = construction?.cost ?? Infinity;
    const terrace = game.terraceRulesVersion===1 && (construction?.tileIds.length??0)>1;
    const move = this.state.visualCue;
    const motion: MotionCue | null =
      move?.actorId && move.path.length
        ? {
            actorId: move.actorId,
            fromTileId:
              game.map.route[
                (game.map.route.indexOf(move.path[move.path.length - 1]) -
                  move.path.length +
                  game.map.route.length) %
                  game.map.route.length
              ],
            path: move.path,
            nonce: move.revision,
          }
        : null;
    let heading =
      game.phase === "await_roll"
        ? "准备出发"
        : game.phase === "await_decision"
          ? "这块土地，值得投资吗？"
          : visit
            ? terrace ? "一起建设这一排街坊" : "为你的小镇添一栋房"
            : "这一步，已经办妥";
    if (busy)
      heading = motion
        ? "正在沿街区前进…"
        : this.state.rentCue
          ? "正在支付租金…"
          : "小镇传来新消息…";
    else if (this.state.awaitingHandoff) heading = `轮到 ${current.name}`;
    else if (current.kind === "computer")
      heading = this.state.cpuPaused ? "电脑已暂停" : "电脑正在行动…";
    else if (current.detention)
      heading = `${current.detention.kind === "hospital" ? "医院休养" : "监狱停留"} · 剩余 ${current.detention.remaining} 回合`;
    else if (game.phase === "await_shop") heading = "小镇道具商店";
    const ownedCards = Object.values(current.cards ?? {}).reduce(
      (sum, n) => sum + (n ?? 0),
      0,
    );
    return (
      <main
        className="app-shell"
        data-game-status={game.status}
        data-game-phase={this.state.game.phase}
        data-game-revision={this.state.game.revision}
        data-map-id={game.map.id}
        data-presenting={String(busy)}
        data-die-nonce={this.state.dieNonce}
        data-scene-step={this.state.visualCue?.step ?? 0}
        data-die-actor={this.state.dieActorId ?? ""}
        onClickCapture={(event) => {
          if (event.detail > 1 && !(event.target instanceof Element && event.target.closest(".world-navigation"))) {
            event.preventDefault();
            event.stopPropagation();
          }
        }}
        onKeyDownCapture={(event) => {
          if (event.repeat && (event.key === "Enter" || event.key === " ")) {
            event.preventDefault();
            event.stopPropagation();
          }
        }}
      >
        <section
          className="board-card"
          aria-label={`${game.tiles.length} 格游戏棋盘`}
        >
          <MeasuredWorld
            key={this.state.sceneEpoch}
            game={game}
            motion={motion}
            dieValue={
              this.state.dieActorId === current.id ? this.state.dieValue : null
            }
            dieNonce={this.state.dieNonce}
            reducedMotion={this.noMotion}
            followCurrent={this.state.cameraFollow}
            onFollowCurrentChange={this.setCameraFollow}
            rent={this.state.rentCue}
            outcome={this.state.outcomeCue}
            pendingBankruptIds={
              this.state.outcomeCue?.stage === "bankrupt" &&
              this.state.outcomeCue.actorId
                ? [this.state.outcomeCue.actorId]
                : []
            }
            paused={this.state.overlay !== null && !busy}
            onMotionComplete={this.finishSceneMotion}
            onActorStep={this.onActorStep}
            onSelectTile={this.onSceneTileSelect}
            selectedTileId={this.state.selectedTileId}
            onReadyChange={this.onSceneReadyChange}
          />
        </section>
        <header className="game-top">
          <div className="game-place">
            <span className="brand-mark">富</span>
            <div>
              <strong>
                {LEVELS.find(level => level.map.id === game.map.id)?.name ?? "自定义地图"}
              </strong>
              <small>大富翁 · 本机对局</small>
            </div>
          </div>
          <div className="round-indicator">
            第 <b>{game.round}</b>{game.endCondition==='bankruptcy'?' 轮 · 破产决胜':` / ${game.maxRounds} 轮`}
          </div>
          <nav>
            <button
              className="camera-toggle"
              aria-pressed={this.state.cameraFollow}
              onClick={this.toggleCamera}
            >
              {this.state.cameraFollow ? "跟随" : "全景"}
            </button>
            <button
              className="menu-toggle"
              onClick={() => this.openOverlay("menu")}
            >
              菜单 <span>☰</span>
            </button>
          </nav>
        </header>
        <section
          className="player-roster asset-quick-roster"
          aria-label="玩家状态"
        >
          {game.players.map((p, i) => (
            <button
              className={`player-card${current.id === p.id ? " active" : ""}`}
              key={p.id}
              data-player-id={p.id}
              title={`${p.name} · 现金 ${p.cash.toLocaleString("zh-CN")}`}
              style={
                { "--seat-color": MASCOT_SEAT_COLORS[i] } as React.CSSProperties
              }
              onClick={() => this.openOverlay("assets")}
            >
              <SeatAvatar seat={i} small />
              <span className="player-copy">
                <span>
                  <strong>{p.name}</strong>
                  <small>
                    {p.bankrupt
                      ? "破产"
                      : game.status === "finished"
                        ? (p.id === game.winnerId ? "获胜" : "已结束")
                      : p.id === current.id
                        ? "行动中"
                        : p.kind === "computer"
                          ? "电脑"
                          : "真人"}
                  </small>
                </span>
                <span className="player-cash">
                  现金 <b>{compactCash(p.cash)}</b>
                </span>
              </span>
            </button>
          ))}
        </section>
        <div className="action-dock">
          <nav className="hud-tools" aria-label="玩家工具">
            <button onClick={() => this.openOverlay("cards")}>
              手牌{ownedCards > 0 && <b>{ownedCards}</b>}
            </button>
            <button onClick={() => this.openOverlay("property")}>地产</button>
            {game.bank && (
              <button onClick={() => this.openOverlay("bank")}>银行</button>
            )}
            {game.market && (
              <button onClick={() => this.openOverlay("stock")}>股票</button>
            )}
          </nav>
          {game.status === "finished" && !busy ? (
            <PostgameSummary
              game={game}
              onDetails={() => this.openOverlay("results")}
              onSave={() => this.openOverlay("saves")}
              onRestart={this.reset}
            />
          ) : (<>
          <section
            className={`turn-card${(human && game.phase === "await_decision") || (human && visit) ? " decision-card" : ""}`}
            aria-label="当前行动"
          >
            <div className="action-copy">
              <span className="action-eyebrow">
                {current.name}的回合
                {game.status === "finished" ? " · 对局结束" : ""}
              </span>
              <h2>{heading}</h2>
              {human && game.phase === "await_decision" ? (
                <div className="arrival-details">
                  <strong>{target.title}{game.terraceRulesVersion===1?` · ${propertyBlock(game,target.id)?.title}`:''}</strong>
                  <span>
                    地价 <b>{target.price}</b>
                  </span>
                  <span>
                    租金 <b>{target.rent}</b>
                  </span>
                  <span>
                    购买后现金{" "}
                    <b>
                      {(current.cash - (target.price ?? 0)).toLocaleString(
                        "zh-CN",
                      )}
                    </b>
                  </span>
                </div>
              ) : human && visit ? (
                <div className="arrival-details">
                  <strong>{terrace?`${propertyBlock(game,target.id)?.title} · ${construction!.tileIds.length} 块联排`:target.title}</strong>
                  <span>
                    费用 <b>{cost}</b>
                  </span>
                  <span>
                    {terrace?'整排通行费':'通行费'} {construction!.rentBefore}{" "}
                    → <b>{construction!.rentAfter}</b>
                  </span>
                  {terrace&&<span>补建 {construction!.upgrades.length} 户至 {construction!.level} 级 · 高等级房屋保留</span>}
                </div>
              ) : (
                <p className="action-status">
                  {busy
                    ? motion
                      ? this.state.dieValue !== null
                        ? `掷出 ${this.state.dieValue} 点 · 等角色到达后再决定`
                        : "正在前进"
                      : this.state.rentCue
                        ? `${game.players.find((p) => p.id === this.state.rentCue?.fromId)?.name} → ${game.players.find((p) => p.id === this.state.rentCue?.toId)?.name}`
                        : "请稍候，正在展示结果"
                    : human && game.phase === "await_roll"
                      ? current.detention
                        ? "本回合暂停行动，跳过后交给下一位玩家。"
                        : `${target.title} · ${game.pendingDie ? "已指定 " + game.pendingDie + " 点" : game.pendingMoveBonus ? "额外前进 " + game.pendingMoveBonus + " 格" : ownedCards ? "可先使用手牌，再掷骰。" : "掷骰，看看下一站的机会。"}`
                      : this.state.awaitingHandoff
                        ? "请把设备交给这位玩家。"
                        : this.state.message}
                </p>
              )}
            </div>
            <div className="action-buttons">
              {busy && (
                <button
                  className="secondary-btn motion-skip"
                  onClick={this.skipPresentation}
                >
                  跳过演出
                </button>
              )}
              {this.state.awaitingHandoff && !busy && (
                <button
                  className="primary-btn"
                  onClick={this.acknowledgeHandoff}
                >
                  我已就位，开始操作
                </button>
              )}
              {human && game.phase === "await_roll" && (
                <button
                  className="primary-btn"
                  key="roll"
                  disabled={!this.state.sceneReady}
                  onClick={() =>
                    this.dispatch(current.detention ? "skip_turn" : "roll")
                  }
                >
                  {current.detention ? "跳过当前停留回合" : "掷骰前进"}{" "}
                  <span>→</span>
                </button>
              )}
              {human && game.phase === "await_decision" && (
                <>
                  <button
                    className="secondary-btn"
                    key="decline"
                    onClick={() => this.dispatch("decline_property")}
                  >
                    暂不购买
                  </button>
                  <button
                    className="primary-btn"
                    key="buy"
                    disabled={current.cash < (target.price ?? 0)}
                    onClick={() => this.dispatch("buy_property")}
                  >
                    购买地产 · {target.price}
                  </button>
                </>
              )}
              {human && visit && (
                <>
                  <button
                    className="secondary-btn"
                    key="skip-build"
                    onClick={() => this.dispatch("end_turn")}
                  >
                    暂不建设
                  </button>
                  <button
                    className="primary-btn"
                    key="build"
                    disabled={current.cash < cost}
                    onClick={() => this.dispatch("upgrade_property", target.id)}
                  >
                    {terrace ? `联排${construction!.level===1?'建造':'升级'} ${construction!.upgrades.length} 户` : (target.level ?? 0) === 0 ? "建造住宅" : "升级房屋"} ·{" "}
                    {cost}
                  </button>
                </>
              )}
              {human && game.phase === "await_end_turn" && !visit && (
                <button
                  className="primary-btn finish-turn"
                  key="end"
                  onClick={() => this.dispatch("end_turn")}
                >
                  结束当前回合 <span>→</span>
                </button>
              )}
              {human && game.phase === "await_shop" && (
                <>
                  <button onClick={() => this.openOverlay("cards")}>
                    查看手牌
                  </button>
                  <button
                    className="primary-btn"
                    onClick={() => this.dispatch("leave_shop")}
                  >
                    离开商店
                  </button>
                </>
              )}
              {current.kind === "computer" &&
                !busy &&
                game.status === "playing" && (
                  <>
                    <button onClick={this.toggleCpuPause}>
                      {this.state.cpuPaused ? "继续电脑" : "暂停电脑"}
                    </button>
                    <button onClick={this.toggleCpuFast}>
                      {this.state.fastMode ? "恢复正常速度" : "快进电脑"}
                    </button>
                  </>
                )}
            </div>
            {human &&
              game.phase === "await_decision" &&
              current.cash < (target.price ?? 0) && (
                <p className="action-error">现金不足，可以暂不购买。</p>
              )}
            {human && visit && current.cash < cost && (
              <p className="action-error">现金不足，本次可暂不建设。</p>
            )}
          </section>
          {human && game.phase === "await_shop" && (
            <div className="shop-offers">
              {(
                [
                  "reward",
                  "stride",
                  "remote",
                  "roadblock",
                  "rent_free",
                ] as const
              ).map((k) => {
                const shop = game.shops?.find(
                    (s) => s.tileId === current.position,
                  ),
                  price = game.facilityRules?.prices[k] ?? Infinity;
                return (
                  <button
                    key={k}
                    disabled={
                      (shop?.cards[k] ?? 0) < 1 ||
                      current.cash < price ||
                      ownedCards >= (game.cardRules?.maxHand ?? 3)
                    }
                    onClick={() => this.dispatch("buy_shop_card", undefined, k)}
                  >
                    {this.cardName(k)} · {price}
                    <small>剩余 {shop?.cards[k] ?? 0}</small>
                  </button>
                );
              })}
            </div>
          )}
          </>)}
        </div>
        {this.state.selectedTileId !== null && !busy && (
          <aside className="board-inspector">
            <button
              aria-label="关闭地块详情"
              onClick={() => this.setState({ selectedTileId: null })}
            >
              ×
            </button>
            <strong>
              {this.state.selectedTileId + 1} ·{" "}
              {game.tiles[this.state.selectedTileId].title}
            </strong>
            <span>
              {game.tiles[this.state.selectedTileId].kind === "property"
                ? `地价 ${game.tiles[this.state.selectedTileId].price} · ${game.tiles[this.state.selectedTileId].ownerId ? game.players.find((p) => p.id === game.tiles[this.state.selectedTileId!].ownerId)?.name + "所有" : "尚无地主"}`
                : "公共地块"}
              {game.tiles[this.state.selectedTileId].kind === "property" &&
                ` · ${game.tiles[this.state.selectedTileId].level ?? 0} 级${game.tiles[this.state.selectedTileId].mortgaged ? " · 抵押中" : ""}`}
            </span>
            {game.tiles[this.state.selectedTileId].kind==='property' && game.map.id==='lime-garden-30' && <span>
              {propertyBlock(game,this.state.selectedTileId)?.title} · {game.terraceRulesVersion===1
                ? `${propertyRun(game,this.state.selectedTileId).length} 块连地 · 整排通行费 ${propertyRent(game,this.state.selectedTileId)}`
                : '旧版单地块规则'}
            </span>}
          </aside>
        )}
        {this.state.saveStatus.startsWith("自动保存失败") && (
          <div className="save-alert" role="alert">
            {this.state.saveStatus}
            <button onClick={() => this.openOverlay("saves")}>备份存档</button>
          </div>
        )}
        {this.renderOverlay()}
      </main>
    );
  }
}
const root = document.getElementById("root");
if (!root) throw new Error("找不到游戏页面根节点");
createRoot(root).render(<App />);
