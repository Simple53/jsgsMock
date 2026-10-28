import json
import os
import glob

def check_and_merge():
    file_keys = [
        ('习近平总书记教育重要论述', 'xjp'),
        ('高等教育学', 'gdjyx'),
        ('高校教师职业道德规范', 'sdsf'),
        ('高等教育心理学', 'xlx'),
        ('高等教育法律与法规', 'zcfg')
    ]
    
    all_done = True
    full_data = {}
    
    for subj_name, prefix in file_keys:
        subj_qs = []
        for i in range(1, 5):
            part_path = os.path.join('chunks', f'ans_{prefix}_part{i}.json')
            if not os.path.exists(part_path):
                print(f"Missing: {part_path}")
                all_done = False
                continue
            with open(part_path, 'r', encoding='utf-8') as pf:
                chunk = json.load(pf)
                subj_qs.extend(chunk)
                
        print(f"Subject [{subj_name}]: {len(subj_qs)} / 220 answered.")
        if len(subj_qs) == 220:
            full_data[subj_name] = subj_qs
        else:
            all_done = False
            
    if all_done:
        # Write to final official quiz data
        with open('quiz_data_official_2026.json', 'w', encoding='utf-8') as out_f:
            json.dump(full_data, out_f, ensure_ascii=False, indent=2)
            
        # Also generate web/quiz_data_official_2026.js
        with open('web/quiz_data_official_2026.js', 'w', encoding='utf-8') as out_js:
            out_js.write("window.OFFICIAL_2026_QUIZ_DATA = " + json.dumps(full_data, ensure_ascii=False) + ";\n")
            
        print("ALL 5 SUBJECTS (1100 QUESTIONS) SUCCESSFULLY MERGED!")
        return True
    return False

if __name__ == '__main__':
    check_and_merge()
