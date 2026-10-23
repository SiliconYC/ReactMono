# ◑ 导入
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import tree_sitter_cpp
from tree_sitter import Language, Node, Parser


# ◕ 功能
class 源码清单_类:
    """
    用 C++ 语法树记录定义和本地头依赖，不以正则计数冒充语义覆盖。

    更新日志：
    2026.10.23 - 建立固定源码可重现清单。
    """

    @staticmethod
    def _节点(arg_节点: Node) -> list[Node]:
        return [arg_节点] + [后代 for 子 in arg_节点.children for 后代 in 源码清单_类._节点(子)]

    @classmethod
    def api_生成(
        cls,
        arg_源码: Path,
        arg_输出: Path,
        arg_映射: Path | None = None,
    ) -> None:
        版本 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版本 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("参考版本不符")
        解析器 = Parser(Language(tree_sitter_cpp.language()))
        文件表 = []
        函数表 = []
        for 路径 in sorted(arg_源码.rglob("*")):
            if not 路径.is_file() or 路径.suffix not in {
                ".cpp",
                ".hpp",
                ".h",
                ".c",
                ".inc",
                ".mm",
                ".m",
            }:
                continue
            相对 = 路径.relative_to(arg_源码).as_posix()
            if 相对.split("/")[0] not in {"src", "include", "tools", "tests", "android", "ios"}:
                continue
            数据 = 路径.read_bytes()
            根 = 解析器.parse(数据).root_node
            文件表.append(
                {
                    "path": 相对,
                    "lines": len(数据.splitlines()),
                    "sha256": hashlib.sha256(数据).hexdigest(),
                    "includes": re.findall(r'#include\s*"([^"]+)"', 数据.decode()),
                    "parser_has_error": 根.has_error,
                }
            )
            for 节点 in cls._节点(根):
                if 节点.type != "function_definition":
                    continue
                声明 = 节点.child_by_field_name("declarator")
                if 声明 is None:
                    raise ValueError(f"未识别的函数声明 {相对}:{节点.start_point.row + 1}")
                函数表.append(
                    {
                        "id": f"{相对}:{节点.start_point.row + 1}",
                        "declarator": 声明.text.decode(),
                        "end_line": 节点.end_point.row + 1,
                        "python": [],
                        "status": "未移植",
                        "evidence": [],
                    }
                )
        if arg_映射 is not None:
            映射 = json.loads(arg_映射.read_text())
            for 函数 in 函数表:
                if 函数["id"] in 映射:
                    函数.update(映射[函数["id"]])
        结果 = {
            "reference": 版本,
            "parser": "tree-sitter-cpp 0.23.4 / tree-sitter 0.25.2",
            "scope": "C/C++/ObjC in src/include/tools/tests/android/ios; lexical definitions",
            "files": 文件表,
            "functions": 函数表,
        }
        arg_输出.parent.mkdir(parents=True, exist_ok=True)
        arg_输出.write_text(json.dumps(结果, ensure_ascii=False, indent=2) + "\n")
        print(f"[完成] {len(文件表)} 个源码文件，{len(函数表)} 个语法函数定义。")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--output", type=Path, required=True)
    参数.add_argument("--mapping", type=Path)
    选项 = 参数.parse_args()
    源码清单_类.api_生成(选项.source, 选项.output, 选项.mapping)
