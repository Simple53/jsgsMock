import os
import re
import json
from bs4 import BeautifulSoup

def format_blanks(text):
    if not text:
        return ''
    text = re.sub(r'^\s*[\t_]+\s*', '______', text)
    text = re.sub(r'^ {2,}', '______', text)
    text = re.sub(r'^[（\(][\s\t_]*[）\)]\s*', '______', text)
    text = re.sub(r'([（\(])[\s\t_]*([）\)])', r'\1______\2', text)
    text = re.sub(r'\t+', '______', text)
    text = re.sub(r' {2,}', '______', text)
    text = re.sub(r'_{2,}', '______', text)
    return text.strip()

def normalize_text(s):
    if not s:
        return ''
    return re.sub(r'[\s_—\t\r\n\.,，。、“”\"\'：:\(\)（）\?？]+', '', s).strip()

def parse_html_subject(file_path, subject_name):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form')
    if not form:
        raise ValueError(f"No form found in {file_path}")
    
    questions = []
    current_type = None
    type_code = None
    
    global_idx = 0
    type_counts = {'单选题': 0, '多选题': 0, '判断题': 0}
    
    for child in form.children:
        if not child.name:
            continue
        classes = child.get('class', [])
        if 'test_content' in classes:
            title_text = child.get_text(strip=True)
            if '单选题' in title_text:
                current_type = '单选题'
                type_code = 'single'
            elif '多选题' in title_text:
                current_type = '多选题'
                type_code = 'multi'
            elif '判断题' in title_text:
                current_type = '判断题'
                type_code = 'judge'
        elif 'test_content_nr' in classes and current_type:
            ul = child.find('ul')
            if not ul:
                continue
            lis = ul.find_all('li', recursive=False)
            for li in lis:
                tt = li.find(class_='test_content_nr_tt')
                if not tt:
                    continue
                font = tt.find('font')
                raw_stem = font.get_text(strip=True) if font else tt.get_text(strip=True)
                stem = format_blanks(raw_stem)
                
                opts = {}
                main = li.find(class_='test_content_nr_main')
                if main:
                    opt_lis = main.find_all(class_='option')
                    for opt_li in opt_lis:
                        opt_text = opt_li.get_text(separator=' ', strip=True)
                        match_choice = re.match(r'^([A-D])[\.、\s]*(.*)', opt_text)
                        if match_choice:
                            letter = match_choice.group(1)
                            opts[letter] = match_choice.group(2).strip()
                        elif opt_text in ['对', '正确']:
                            opts['A'] = '对'
                        elif opt_text in ['错', '错误']:
                            opts['B'] = '错'
                            
                global_idx += 1
                type_counts[current_type] += 1
                
                questions.append({
                    'subject': subject_name,
                    'type': type_code,
                    'typeName': current_type,
                    'num': type_counts[current_type],
                    'globalNum': global_idx,
                    'question': stem,
                    'options': opts,
                    'officialId': li.get('id', '').replace('qu_', '')
                })
                
    return questions

def main():
    folder = r'D:\1_Projects\03_工作_南师大辅导员\00_个人材料\12_高校教资\题库\2026下半年官网'
    
    file_map = [
        ('202610_习近平重要论述.html', '习近平总书记教育重要论述', 'raw_official_2026_xjp.json'),
        ('202610_高等教育学.html', '高等教育学', 'raw_official_2026_gdjyx.json'),
        ('202610_高等教育师德师风.html', '高校教师职业道德规范', 'raw_official_2026_sdsf.json'),
        ('202610_高等教育心理学.html', '高等教育心理学', 'raw_official_2026_xlx.json'),
        ('202610_高等教育政策法规.html', '高等教育法律与法规', 'raw_official_2026_zcfg.json')
    ]
    
    # Also load existing database to pre-match any already verified questions
    with open('quiz_data.json', 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
        
    for fname, sname, outname in file_map:
        fpath = os.path.join(folder, fname)
        qs = parse_html_subject(fpath, sname)
        print(f"Subject [{sname}]: parsed {len(qs)} questions.")
        
        # Pre-match with existing data
        ex_list = existing_data.get(sname, [])
        ex_map = {normalize_text(q['question']): q for q in ex_list}
        
        matched_count = 0
        for q in qs:
            norm_k = normalize_text(q['question'])
            if norm_k in ex_map:
                matched_q = ex_map[norm_k]
                q['answer'] = matched_q.get('answer', '')
                q['analysis'] = matched_q.get('analysis', '')
                q['isAiAnswer'] = False
                q['tags'] = ['2026官网真题', '官方标准答案']
                matched_count += 1
            else:
                q['answer'] = ''
                q['analysis'] = ''
                q['isAiAnswer'] = True
                q['tags'] = ['2026官网模拟', 'AI参考答案']
                
        print(f"  -> Matched with verified answers: {matched_count}, Need AI answers: {len(qs) - matched_count}")
        with open(outname, 'w', encoding='utf-8') as out_f:
            json.dump(qs, out_f, ensure_ascii=False, indent=2)
            
    print("\nAll 5 raw official question files generated successfully.")

if __name__ == '__main__':
    main()
