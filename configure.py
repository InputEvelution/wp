#!/usr/bin/env python3

###
# Generates build files for the project.
# This file also includes the project configuration,
# such as compiler flags and the object matching status.
#
# Usage:
#   python3 configure.py
#   ninja
#
# Append --help to see available options.
###

import sys
import argparse

from pathlib import Path
from tools.project import (
    Object,
    ProjectConfig,
    calculate_progress,
    generate_build,
    is_windows,
)

# Game versions
DEFAULT_VERSION = 2
VERSIONS = [
    "SUPJ01-R0",	# 0
    "SUPJ01-R1",	# 1
    "SUPP01",		# 2
    "SUPE01",		# 3
    "SUPK01",		# 4
]

if len(VERSIONS) > 1:
    versions_str = ", ".join(VERSIONS[:-1]) + f" or {VERSIONS[-1]}"
else:
    versions_str = VERSIONS[0]

parser = argparse.ArgumentParser()
parser.add_argument(
    "mode",
    default="configure",
    help="configure or progress (default: configure)",
    nargs="?",
)
parser.add_argument(
    "--version",
    dest="version",
    default=VERSIONS[DEFAULT_VERSION],
    help=f"version to build ({versions_str})",
)
parser.add_argument(
    "--build-dir",
    dest="build_dir",
    type=Path,
    default=Path("build"),
    help="base build directory (default: build)",
)
parser.add_argument(
    "--compilers",
    dest="compilers",
    type=Path,
    help="path to compilers (optional)",
)
parser.add_argument(
    "--map",
    dest="map",
    action="store_true",
    help="generate map file(s)",
)
parser.add_argument(
    "--debug",
    dest="debug",
    action="store_true",
    help="build with debug info (non-matching)",
)
if not is_windows():
    parser.add_argument(
        "--wrapper",
        dest="wrapper",
        type=Path,
        help="path to wibo or wine (optional)",
    )
parser.add_argument(
    "--build-dtk",
    dest="build_dtk",
    type=Path,
    help="path to decomp-toolkit source (optional)",
)
parser.add_argument(
    "--sjiswrap",
    dest="sjiswrap",
    type=Path,
    help="path to sjiswrap.exe (optional)",
)
parser.add_argument(
    "--verbose",
    dest="verbose",
    action="store_true",
    help="print verbose output",
)
args = parser.parse_args()

config = ProjectConfig()
config.version = args.version.upper()
if config.version not in VERSIONS:
    sys.exit(f"Invalid version '{config.version}', expected {versions_str}")
version_num = VERSIONS.index(config.version)

# Apply arguments
config.build_dir = args.build_dir
config.build_dtk_path = args.build_dtk
config.compilers_path = args.compilers
config.debug = args.debug
config.generate_map = args.map
config.sjiswrap_path = args.sjiswrap
if not is_windows():
    config.wrapper = args.wrapper

# Tool versions
config.compilers_tag = "20240706"
config.dtk_tag = "v0.9.2"
config.sjiswrap_tag = "v1.1.1"
config.wibo_tag = "0.6.11"

# Project
config.config_path = Path("config") / config.version / "config.yml"
config.check_sha_path = Path("orig") / f"{config.version}.sha1"
config.ldflags = [
    "-fp hardware",
    "-nodefaults",
    "-listclosure",
]

# Base flags, common to most GC/Wii games.
# Generally leave untouched, with overrides added below.
cflags_base = [
    "-nodefaults",
    "-proc gekko",
    "-align powerpc",
    "-enum int",
    "-fp hardware",
    "-Cpp_exceptions off",
    # "-W all",
    "-O4,p",
    "-inline auto",
    '-pragma "cats off"',
    '-pragma "warn_notinlined off"',
    "-maxerrors 1",
    "-nosyspath",
    "-RTTI off",
    "-fp_contract on",
    "-str reuse",
    "-i include",
	"-enc SJIS",
    "-func_align 16",
    f"-DVERSION={version_num}",
]

# Debug flags
if config.debug:
    cflags_base.extend(["-sym on", "-DDEBUG=1"])
else:
    cflags_base.append("-DNDEBUG=1")

# Metrowerks library flags
cflags_runtime = [
    *cflags_base,
    "-use_lmw_stmw on",
    "-str pool,readonly,reuse",
    "-gccinc",
    "-common off",
	"-inline auto",
    "-func_align 4",
]

# REL flags
cflags_rel = [
    *cflags_base,
    "-sdata 0",
    "-sdata2 0",
]

config.linker_version = "Wii/1.3"


# Helper function for Revolution libraries
def RevolutionLib(lib_name, objects):
    return {
        "lib": lib_name,
        "mw_version": "Wii/1.0",
        "cflags": cflags_base,
        "host": False,
        "objects": objects,
    }


# Helper function for NW4R libraries
def NW4RLib(lib_name, objects):
    return {
        "lib": lib_name,
        "mw_version": "Wii/1.1",
        "cflags": cflags_base,
        "host": False,
        "objects": objects,
    }


# Helper function for RELs
def Rel(lib_name, objects):
    return {
        "lib": lib_name,
        "mw_version": config.linker_version,
        "cflags": cflags_rel,
        "host": True,
        "objects": objects,
    }


Matching = True
NonMatching = False

config.warn_missing_config = True
config.warn_missing_source = False
config.libs = [
    {
        "lib": "wp",
        "mw_version": config.linker_version,
        "cflags": cflags_base,
        "host": False,
        "objects": [
            Object(NonMatching, "wp/frand.c"),
        ],
    },
    {
        "lib": "homebuttonLib",
        "mw_version": "Wii/1.0",
        "cflags": cflags_rel,
        "host": False,
        "objects": [
            Object(NonMatching, "Revolution/HBM/HBMFrameController.cpp"),
            Object(NonMatching, "Revolution/HBM/HBMAnmController.cpp"),
            Object(NonMatching, "Revolution/HBM/HBMGUIManager.cpp"),
            Object(NonMatching, "Revolution/HBM/HBMController.cpp"),
            Object(NonMatching, "Revolution/HBM/HBMRemoteSpk.cpp"),
            Object(NonMatching, "Revolution/HBM/HBMAxSound.cpp"),
            Object(NonMatching, "Revolution/HBM/HBMCommon.cpp"),
            Object(NonMatching, "Revolution/HBM/HBMBase.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_animation.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_arcResourceAccessor.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_bounding.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_common.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_drawInfo.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_group.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_layout.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_material.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_pane.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_picture.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_resourceAccessor.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_textBox.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/lyt/lyt_window.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/math/math_triangular.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/ut/ut_binaryFileFormat.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/ut/ut_CharStrmReader.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/ut/ut_CharWriter.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/ut/ut_Font.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/ut/ut_LinkList.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/ut/ut_list.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/ut/ut_ResFont.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/ut/ut_ResFontBase.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/ut/ut_TagProcessorBase.cpp"),
            Object(NonMatching, "Revolution/HBM/nw4hbm/ut/ut_TextWriterBase.cpp"),
            Object(NonMatching, "Revolution/HBM/mix.cpp"),
            Object(NonMatching, "Revolution/HBM/syn.cpp"),
            Object(NonMatching, "Revolution/HBM/synctrl.cpp"),
            Object(NonMatching, "Revolution/HBM/synenv.cpp"),
            Object(NonMatching, "Revolution/HBM/synmix.cpp"),
            Object(NonMatching, "Revolution/HBM/synpitch.cpp"),
            Object(NonMatching, "Revolution/HBM/synsample.cpp"),
            Object(NonMatching, "Revolution/HBM/synvoice.cpp"),
            Object(NonMatching, "Revolution/HBM/seq.cpp"),
        ],
    },
    {
        "lib": "RVLFaceLib",
        "mw_version": "Wii/1.0",
        "cflags": cflags_base,
        "host": False,
        "objects": [
            Object(NonMatching, "RVLFaceLib/RFL_System.c"),
            Object(NonMatching, "RVLFaceLib/RFL_NANDLoader.c"),
            Object(NonMatching, "RVLFaceLib/RFL_NANDAccess.c"),
            Object(NonMatching, "RVLFaceLib/RFL_Model.c"),
            Object(NonMatching, "RVLFaceLib/RFL_MakeTex.c"),
            Object(NonMatching, "RVLFaceLib/RFL_Icon.c"),
            Object(NonMatching, "RVLFaceLib/RFL_HiddenDatabase.c"),
            Object(NonMatching, "RVLFaceLib/RFL_Database.c"),
            Object(NonMatching, "RVLFaceLib/RFL_Controller.c"),
            Object(NonMatching, "RVLFaceLib/RFL_MiddleDatabase.c"),
            Object(NonMatching, "RVLFaceLib/RFL_DefaultDatabase.c"),
            Object(NonMatching, "RVLFaceLib/RFL_DataUtility.c"),
            Object(NonMatching, "RVLFaceLib/RFL_Format.c"),
        ],
    },
    NW4RLib(
        "ef",
        [
            Object(NonMatching, "NW4R/ef/ef_draworder.cpp"),
            Object(NonMatching, "NW4R/ef/ef_effect.cpp"),
            Object(NonMatching, "NW4R/ef/ef_effectsystem.cpp"),
            Object(NonMatching, "NW4R/ef/ef_emitter.cpp"),
            Object(NonMatching, "NW4R/ef/ef_animcurve.cpp"),
            Object(NonMatching, "NW4R/ef/ef_postfield.cpp"),
            Object(NonMatching, "NW4R/ef/ef_particle.cpp"),
            Object(NonMatching, "NW4R/ef/ef_particlemanager.cpp"),
            Object(NonMatching, "NW4R/ef/ef_resource.cpp"),
            Object(NonMatching, "NW4R/ef/ef_util.cpp"),
            Object(NonMatching, "NW4R/ef/ef_handle.cpp"),
            Object(NonMatching, "NW4R/ef/ef_emitterform.cpp"),
            Object(NonMatching, "NW4R/ef/ef_creationqueue.cpp"),
            Object(NonMatching, "NW4R/ef/ef_emform.cpp"),
            Object(NonMatching, "NW4R/ef/ef_point.cpp"),
            Object(NonMatching, "NW4R/ef/ef_line.cpp"),
            Object(NonMatching, "NW4R/ef/ef_disc.cpp"),
            Object(NonMatching, "NW4R/ef/ef_sphere.cpp"),
            Object(NonMatching, "NW4R/ef/ef_cylinder.cpp"),
            Object(NonMatching, "NW4R/ef/ef_torus.cpp"),
            Object(NonMatching, "NW4R/ef/ef_cube.cpp"),
            Object(NonMatching, "NW4R/ef/ef_drawstrategybuilder.cpp"),
            Object(NonMatching, "NW4R/ef/ef_drawstrategyimpl.cpp"),
            Object(NonMatching, "NW4R/ef/ef_drawbillboardstrategy.cpp"),
            Object(NonMatching, "NW4R/ef/ef_drawdirectionalstrategy.cpp"),
            Object(NonMatching, "NW4R/ef/ef_drawfreestrategy.cpp"),
            Object(NonMatching, "NW4R/ef/ef_drawlinestrategy.cpp"),
            Object(NonMatching, "NW4R/ef/ef_drawpointstrategy.cpp"),
            Object(NonMatching, "NW4R/ef/ef_drawstripestrategy.cpp"),
            Object(NonMatching, "NW4R/ef/ef_drawsmoothstripestrategy.cpp"),
            Object(NonMatching, "NW4R/ef/ef_res_emitter_ac.cpp"),
            Object(NonMatching, "NW4R/ef/ef_res_emitterparam_ac.cpp"),
            # TODO: Figure out names for other ef_res funcs
        ],
    ),
	{
        "lib": "Runtime.PPCEABI.H",
        "mw_version": "Wii/1.0RC1",
        "cflags": cflags_runtime,
        "host": False,
        "objects": [
            Object(Matching, "Runtime.PPCEABI.H/global_destructor_chain.c"),
            Object(Matching, "Runtime.PPCEABI.H/__init_cpp_exceptions.cpp"),
            # TODO: need to implement all
        ],
    },
    # TODO: RELs
    {
        "lib": "REL",
        "mw_version": config.linker_version,
        "cflags": cflags_rel,
        "host": False,
        "objects": [
            Object(
                Matching,
                "REL/global_destructor_chain.c",
                source="Runtime.PPCEABI.H/global_destructor_chain.c",
            ),
        ],
    },
]

if args.mode == "configure":
    # Write build.ninja and objdiff.json
    generate_build(config)
elif args.mode == "progress":
    # Print progress and write progress.json
    config.progress_each_module = args.verbose
    calculate_progress(config)
else:
    sys.exit("Unknown mode: " + args.mode)