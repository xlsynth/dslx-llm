import os

XLSYNTH_TOOLS_DIR = os.environ['XLSYNTH_TOOLS']
DSLX_INTERPRETER_MAIN = os.path.join(XLSYNTH_TOOLS_DIR, 'dslx_interpreter_main')
TYPECHECK_MAIN = os.path.join(XLSYNTH_TOOLS_DIR, 'typecheck_main')
DSLX_STDLIB_PATH = os.path.join(XLSYNTH_TOOLS_DIR, 'xls', 'dslx', 'stdlib')
assert os.path.isdir(DSLX_STDLIB_PATH), f'DSLX_STDLIB_PATH must be a directory: {DSLX_STDLIB_PATH}'
