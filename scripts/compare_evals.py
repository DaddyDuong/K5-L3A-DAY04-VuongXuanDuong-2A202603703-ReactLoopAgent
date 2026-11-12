"""Đọc hai báo cáo đầy đủ, kiểm tra cấu hình và tổng hợp; không sửa điểm eval."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def metrics(report):
    agent_usage = [u for case in report['cases'] for u in case['result']['usage']]
    judge_usage = [case['grade']['judge_usage'] for case in report['cases']
                   if case['grade'].get('judge_usage')]
    usage = agent_usage + judge_usage
    return {
        'score': report['summary']['score_0_100'],
        'agent_model_calls': len(agent_usage),
        'judge_calls_with_usage': len(judge_usage),
        'tool_calls': sum(event.get('event') == 'tool' for case in report['cases']
                          for event in case['result']['trace']),
        'prompt_tokens': sum(u.get('prompt_tokens', 0) for u in usage),
        'completion_tokens': sum(u.get('completion_tokens', 0) for u in usage),
        'total_tokens': sum(u.get('total_tokens', 0) for u in usage),
        'reported_cost_usd': round(sum(u.get('cost', 0) or 0 for u in usage), 10),
    }


def compare(before, after):
    if before['config'] != after['config']:
        raise ValueError('Hai báo cáo khác cấu hình; không dùng làm so sánh trước/sau.')
    expected_ids = {c['id'] for c in json.loads((ROOT / 'evals' / 'cases.json').read_text())}
    for report in (before, after):
        cases = report['cases']
        if (len(cases) != len(expected_ids) or {c['id'] for c in cases} != expected_ids
                or any(c['grade'].get('status') != 'scored' for c in cases)
                or report['summary']['score_0_100'] is None):
            raise ValueError('Cần đủ 22 case được chấm trong từng báo cáo.')
    previous = {case['id']: case for case in before['cases']}
    per_case = []
    for case in after['cases']:
        old_score = previous[case['id']]['grade']['score']
        new_score = case['grade']['score']
        per_case.append({'id': case['id'], 'before': old_score, 'after': new_score,
                         'delta': new_score - old_score})
    return {'config': before['config'], 'before': metrics(before), 'after': metrics(after),
            'per_case': per_case}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', default='eval_before.json')
    parser.add_argument('--after', default='eval_after.json')
    args = parser.parse_args()
    reports = [json.loads(Path(path).read_text()) for path in (args.before, args.after)]
    print(json.dumps(compare(*reports), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
