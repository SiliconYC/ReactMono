# 原查表投影与渲染快照

固定依据 `board_renderer.hpp`、`src/board_renderer.cpp` 的投影/姿态选择，以及 `src/board_projection_tables.inc`。Python 对应 `board_models.py/board_projection.py/projection_tables.py`；渲染快照不执行或改变游戏规则。

## 常量来源与复现

沿用 Iru Cai/mytbk 逆向的公开GPL常量：八视角各841个29×29相机格点、各304个地面遍历项，以及八组四分量小数基底。不使用连续浮点矩阵重算。提取工具把C++ `(x,y)` 常量还原成原表字节序 `(y,x)` 后，核对原记录SHA256：

`396188ec0d57d5fd4b5fa021890d0cc57b2ffb0cf42d53a65623a08fadafe1d7`

输出是可审查的Python整数/元组字面量，不包含商业MKF、EXE、纹理或隐藏引擎。表格保持紧凑布局；这些标量表行数不能当作手写游戏逻辑规模或体验完成率。

```sh
uv run --project pygame python pygame/tools/extract_projection_tables.py \
  --source /path/to/pinned-cpp --output /tmp/projection_tables.py
```

## 坐标与姿态

棋盘点为 `(x,y)`，区别于地形扫描器的 `(y,x)` 四边形。世界坐标先按32单位向下取整定位瓦片，相机周边超出±14瓦片返回空。小数部分X、Y各自按对应基底向下取整后相加，不能先相加再取整。投影可落到视口外，最终绘制再裁剪。

反投影只接收视口内点，按原先Y后X的顺序穷举29×29瓦片中心，严格更近时更新；等距保留先出现项。它返回最近瓦片中心，不是连续逆矩阵。

角色资源按原优先级选21姿态组：非投骰的特殊姿态、受伤、梦游、水上、交通。梦游投骰使用步行投骰资源；受伤仍优先于投骰。方向分组与动画帧选择由随后场景合成层完成。

## 自动证据与未完成范围

[报告](evidence/projection-differential.json) 包含50184个投影、3000个反投影、10400个角色/交通/状态组合，共63584例，返回或拒绝均与固定C++相同。覆盖全部格点的三组小数、负坐标、int32极值附近、相机错误与所有姿态优先组合。局部13项，完整Python121/121、Ruff通过。

尚未验证实际道路/建筑/角色的合成帧、遮挡、动画时序或图形操作。这不是八图画面完成，更不是完整可玩游戏。

```sh
uv run --project pygame python pygame/tools/differential_projection.py \
  --source /path/to/pinned-cpp --build /tmp/rich4-cpp-core \
  --report /tmp/projection-differential.json
```
