import json
import os

def run():
    with open('eslint_out.json', 'r', encoding='utf-16') as f:
        data = json.load(f)

    for file_result in data:
        file_path = file_result.get('filePath')
        messages = file_result.get('messages', [])
        if not messages:
            continue
            
        print(f"Fixing {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Group messages by line
        line_to_rules = {}
        for m in messages:
            line_idx = m['line'] - 1
            rule = m['ruleId']
            if not rule:
                continue
            if line_idx not in line_to_rules:
                line_to_rules[line_idx] = set()
            line_to_rules[line_idx].add(rule)
            
        # Sort lines descending so insertions don't change previous line indices
        for line_idx in sorted(line_to_rules.keys(), reverse=True):
            rules = sorted(list(line_to_rules[line_idx]))
            rules_str = ", ".join(rules)
            todo_comment = " // TODO: fix" if "no-explicit-any" in rules_str else ""
            
            # Find indentation of the target line
            target_line = lines[line_idx]
            indent = target_line[:len(target_line) - len(target_line.lstrip())]
            
            disable_line = f"{indent}// eslint-disable-next-line {rules_str}{todo_comment}\n"
            lines.insert(line_idx, disable_line)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
    print("Done fixing files.")

if __name__ == '__main__':
    run()
