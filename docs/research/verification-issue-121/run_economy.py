#!/usr/bin/env python3
"""Issue #121: isolated native rent + trade experiments, no browser dependencies."""
import datetime
import json
import pathlib
import runpy
import shutil
import subprocess
import sys
import tempfile

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"evidence"
OUT.mkdir(exist_ok=True)
scope=runpy.run_path(str(HERE/"run.py"))
economy=scope["economy"]
context=economy.__globals__
underlying=context["run"]

def use_headless_sdl(label,args,cwd=context["ROOT"],timeout=240):
    if label=="cmake configure":
        args=list(args)+["-DSDL_UNIX_CONSOLE_BUILD=ON"]
    return underlying(label,args,cwd=cwd,timeout=timeout)

context["run"]=use_headless_sdl
folder=pathlib.Path(tempfile.mkdtemp(prefix="issue121-economy-"))
error=None
try:
    upstream=scope["checkout"]("rich4re",folder)
    if upstream:
        # Temporary compatibility shim for pre-existing upstream GCC/Clang error:
        # nested DisplayConfig with default initializers is invalid as an in-class default argument.
        # This changes ONLY the declaration/call forwarding, never rent/trade production logic.
        header=upstream/"include/game/application.h"
        source=header.read_text(encoding="utf-8")
        before=chr(10).join([
            "    bool init(const std::string& gameDir, bool headless = false,",
            "              const DisplayConfig& display = DisplayConfig{});"
        ])
        replacement=chr(10).join([
            "    bool init(const std::string& gameDir, bool headless,",
            "              const DisplayConfig& display);",
            "    bool init(const std::string& gameDir, bool headless = false) {",
            "        return init(gameDir, headless, DisplayConfig{});",
            "    }"
        ])
        if before not in source:
            raise RuntimeError("Pinned upstream Application::init declaration changed")
        header.write_text(source.replace(before,replacement,1),encoding="utf-8")
        context["log"].append("EPHEMERAL HEADER PATCH: Application::init default argument moved to inline 2-argument overload; unchanged economy implementation")
        (OUT/"compiler-compatibility.patch").write_text(
            "Upstream SHA b7b76570f445ad07c0788314062b8500e77259e7\\n"
            "Source: include/game/application.h\\n"
            "- "+before+"\\n+ "+replacement+"\\n"
            "Only ephemeral test clone is patched; not part of ReactMono business code.\\n",
            encoding="utf-8")
        economy(upstream)
        binary=upstream/"build-issue121"/"rich4_tests"
        if binary.exists():
            use_headless_sdl("native unit stdout", [str(binary)], cwd=upstream,timeout=180)
    else:
        error="Upstream clone/SHA verification failed"
except Exception as exc:
    error=repr(exc)
finally:
    import os
    report=context["report"]
    report["utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    report["source"]="Independent native Ubuntu CMake test of pinned tytannial/rich4-re; no proprietary game assets used"
    report["build_flag"]="SDL_UNIX_CONSOLE_BUILD=ON (no X11/Wayland, dummy-only unit test)"
    report["error"]=error
    steps=report["commands"]
    pass_compile=any(d["label"]=="cmake build unit" and d["exit"]==0 for d in steps)
    pass_ctest=any(d["label"]=="ctest rent/trade" and d["exit"]==0 for d in steps)
    pass_direct=any(d["label"]=="native unit stdout" and d["exit"]==0 for d in steps)
    report["acceptance"]={"compile":pass_compile,"ctest":pass_ctest,"native_unit_stdout":pass_direct,
                          "passed":pass_compile and pass_ctest and pass_direct}
    (OUT/"economy-run.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/"economy-run.log").write_text("\n\n".join(context["log"]),encoding="utf-8")
    shutil.rmtree(folder,ignore_errors=True)
    print("ECONOMY_RESULT",json.dumps(report["acceptance"]),flush=True)

sys.exit(0 if report["acceptance"]["passed"] else 1)
