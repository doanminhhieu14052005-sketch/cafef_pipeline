"""Quick test for _extract_json brace-counting logic."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from module3_summarizer import _extract_json

tests = [
    # (input, expected)
    ('{"summary": ["a"]}', '{"summary": ["a"]}'),
    ('```json\n{"summary": ["a"]}\n```', '{"summary": ["a"]}'),
    ('{"summary": ["a"]}\nHy vong huu ich}', '{"summary": ["a"]}'),
    ('{"key_metrics": {"revenue": "1000"}}', '{"key_metrics": {"revenue": "1000"}}'),
    ('Day la ket qua:\n{"impact": "Positive"}\nXong roi!', '{"impact": "Positive"}'),
    ('{"summary": ["tang {5%} so voi"]}', '{"summary": ["tang {5%} so voi"]}'),
    ('Phan tich:\n{"a": 1}\n{"b": 2}', '{"a": 1}'),
]

passed = 0
for i, (inp, expected) in enumerate(tests, 1):
    result = _extract_json(inp)
    ok = result == expected
    status = "PASS" if ok else "FAIL"
    print(f"Test {i}: {status}")
    if not ok:
        print(f"  Input:    {inp!r}")
        print(f"  Expected: {expected!r}")
        print(f"  Got:      {result!r}")
    else:
        passed += 1

print(f"\n{passed}/{len(tests)} tests passed")
