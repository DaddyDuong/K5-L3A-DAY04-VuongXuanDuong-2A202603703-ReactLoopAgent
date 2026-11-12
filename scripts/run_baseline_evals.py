"""Chạy lại agent trước cải tiến bằng eval runner gốc, không thay agent.py.

Ví dụ: python3 scripts/run_baseline_evals.py --workers 4 --max-steps 8
       --output eval_before_reproduced.json
"""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'evals'))

import run_evals


def main():
    spec = importlib.util.spec_from_file_location('agent_before', ROOT / 'artifacts' / 'agent_before.py')
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    run_evals.run_agent = baseline.run_agent
    return run_evals.main()


if __name__ == '__main__':
    sys.exit(main())
