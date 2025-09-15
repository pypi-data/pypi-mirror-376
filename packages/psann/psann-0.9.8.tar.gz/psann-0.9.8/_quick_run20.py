import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'src'))
from examples._20_runner import run
run()
