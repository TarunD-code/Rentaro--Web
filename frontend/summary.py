import json

with open('eslint_out.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

for file_result in data:
    if file_result.get('messages'):
        file_path = file_result.get('filePath')
        rules = [m.get('ruleId') for m in file_result.get('messages')]
        from collections import Counter
        counts = Counter(rules)
        print(f"{file_path}: {dict(counts)}")
