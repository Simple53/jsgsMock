import docx
import glob
import os
import re
import json

def format_blanks(text):
    if not text:
        return ''
    # 替换各种不规范的填空留空为标准6个下划线 ______
    text = re.sub(r'([（\(])[\s\t_]*([）\)])', r'\1______\2', text)
    text = re.sub(r'\t+', '______', text)
    text = re.sub(r' {2,}', '______', text)
    text = re.sub(r'_{2,}', '______', text)
    return text.strip()

def clean_opt(opt_text):
    if not opt_text:
        return ''
    opt_text = re.sub(r'[\t\r\n]+', ' ', opt_text)
    opt_text = re.sub(r' +', ' ', opt_text)
    return opt_text.strip()

def normalize_text(s):
    if not s:
        return ''
    return re.sub(r'[\s_—\t\r\n\.,，。、“”\"\'：:\(\)（）\?？]+', '', s).strip()

def parse_choice_options(content):
    # 使用增强正则寻找选项前缀 A., B., C., D.
    # 支持中文前缀、无空格前缀如 》D.、实验D.、整合C.
    matches = list(re.finditer(r'(?<![A-Za-z0-9])([A-D])[\.、]\s*', content))
    
    opts_found = {}
    last_pos = -1
    for m in matches:
        letter = m.group(1)
        if letter == 'A' and 'A' not in opts_found:
            opts_found['A'] = m
        elif letter == 'B' and 'B' not in opts_found and m.start() > last_pos:
            opts_found['B'] = m
            last_pos = m.start()
        elif letter == 'C' and 'C' not in opts_found and m.start() > last_pos:
            opts_found['C'] = m
            last_pos = m.start()
        elif letter == 'D' and 'D' not in opts_found and m.start() > last_pos:
            opts_found['D'] = m
            last_pos = m.start()
            
    q_text = ''
    options = {}
    
    # 情况 1: A, B, C, D 全部匹配到
    if all(k in opts_found for k in ['A', 'B', 'C', 'D']):
        mA, mB, mC, mD = opts_found['A'], opts_found['B'], opts_found['C'], opts_found['D']
        q_text = content[:mA.start()].strip()
        options['A'] = clean_opt(content[mA.end():mB.start()])
        options['B'] = clean_opt(content[mB.end():mC.start()])
        options['C'] = clean_opt(content[mC.end():mD.start()])
        options['D'] = clean_opt(content[mD.end():])
        return format_blanks(q_text), options
        
    # 情况 2: 匹配到 B, C, D (缺失 A.)
    if all(k in opts_found for k in ['B', 'C', 'D']):
        mB, mC, mD = opts_found['B'], opts_found['C'], opts_found['D']
        options['B'] = clean_opt(content[mB.end():mC.start()])
        options['C'] = clean_opt(content[mC.end():mD.start()])
        options['D'] = clean_opt(content[mD.end():])
        
        pre_b = content[:mB.start()].strip()
        if '\n' in pre_b:
            lines = [l.strip() for l in pre_b.split('\n') if l.strip()]
            q_text = '\n'.join(lines[:-1]).strip()
            options['A'] = clean_opt(lines[-1])
        elif '\t' in pre_b:
            parts = [p.strip() for p in pre_b.split('\t') if p.strip()]
            q_text = '\t'.join(parts[:-1]).strip()
            options['A'] = clean_opt(parts[-1])
        else:
            puncs = list(re.finditer(r'[。？！\?：:\_]\s*', pre_b))
            if puncs:
                last_punc = puncs[-1]
                q_text = pre_b[:last_punc.end()].strip()
                options['A'] = clean_opt(pre_b[last_punc.end():])
            else:
                q_text = pre_b
                options['A'] = ''
        return format_blanks(q_text), options

    # 情况 3: 匹配到 C, D (缺失 A. 和 B.)
    if all(k in opts_found for k in ['C', 'D']):
        mC, mD = opts_found['C'], opts_found['D']
        options['C'] = clean_opt(content[mC.end():mD.start()])
        options['D'] = clean_opt(content[mD.end():])
        pre_c = content[:mC.start()].strip()
        lines = [l.strip() for l in pre_c.split('\n') if l.strip()]
        if len(lines) >= 3:
            q_text = '\n'.join(lines[:-2]).strip()
            options['A'] = clean_opt(lines[-2])
            options['B'] = clean_opt(lines[-1])
        elif len(lines) == 2:
            q_text = lines[0]
            options['A'] = clean_opt(lines[1])
            options['B'] = ''
        else:
            q_text = pre_c
            options['A'] = ''
            options['B'] = ''
        return format_blanks(q_text), options

    # 情况 4: 匹配到 B (缺失 A, C, D)
    if 'B' in opts_found and 'C' not in opts_found and 'D' not in opts_found:
        mB = opts_found['B']
        pre_b = content[:mB.start()].strip()
        post_b = content[mB.end():].strip()
        if '\n' in pre_b:
            lines = [l.strip() for l in pre_b.split('\n') if l.strip()]
            q_text = '\n'.join(lines[:-1]).strip()
            options['A'] = clean_opt(lines[-1])
        else:
            puncs = list(re.finditer(r'[。？！\?：:\_]\s*', pre_b))
            if puncs:
                last_punc = puncs[-1]
                q_text = pre_b[:last_punc.end()].strip()
                options['A'] = clean_opt(pre_b[last_punc.end():])
            else:
                q_text = pre_b
                options['A'] = ''
        lines_post = [l.strip() for l in post_b.split('\n') if l.strip()]
        if len(lines_post) >= 3:
            options['B'] = clean_opt(lines_post[0])
            options['C'] = clean_opt(lines_post[1])
            options['D'] = clean_opt('\n'.join(lines_post[2:]))
        elif len(lines_post) == 2:
            options['B'] = clean_opt(lines_post[0])
            options['C'] = clean_opt(lines_post[1])
            options['D'] = ''
        else:
            options['B'] = clean_opt(post_b)
            options['C'] = ''
            options['D'] = ''
        return format_blanks(q_text), options

    # 情况 5: 匹配到 D (缺失 A, B, C)
    if 'D' in opts_found and 'B' not in opts_found and 'C' not in opts_found:
        mD = opts_found['D']
        options['D'] = clean_opt(content[mD.end():])
        pre_d = content[:mD.start()].strip()
        lines = [l.strip() for l in pre_d.split('\n') if l.strip()]
        if len(lines) >= 4:
            q_text = '\n'.join(lines[:-3]).strip()
            options['A'] = clean_opt(lines[-3])
            options['B'] = clean_opt(lines[-2])
            options['C'] = clean_opt(lines[-1])
        elif len(lines) == 3:
            q_text = lines[0]
            options['A'] = clean_opt(lines[1])
            options['B'] = clean_opt(lines[2])
            options['C'] = ''
        return format_blanks(q_text), options

    # 情况 6: 完全无 A/B/C/D 标号
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    if len(lines) >= 5:
        q_text = '\n'.join(lines[:-4]).strip()
        options['A'] = clean_opt(lines[-4])
        options['B'] = clean_opt(lines[-3])
        options['C'] = clean_opt(lines[-2])
        options['D'] = clean_opt(lines[-1])
    else:
        q_text = content
        options = {}

    return format_blanks(q_text), options

def extract_q_and_opts(full_content, is_choice=True):
    # 提取答案
    ans_m = re.search(r'正确答案[:：]\s*([A-Da-d对错√×\s]+)', full_content)
    if ans_m:
        ans_raw = ans_m.group(1).strip()
        if any(c in ans_raw for c in ['对', '√', '正确']):
            ans_val = '对'
        elif any(c in ans_raw for c in ['错', '×', '错误']):
            ans_val = '错'
        else:
            ans_val = ''.join(ans_raw.split()).upper()
        content = full_content[:ans_m.start()].strip()
    else:
        ans_val = ''
        content = full_content.strip()
        
    if not is_choice:
        return format_blanks(content), {}, ans_val
        
    q_text, options = parse_choice_options(content)
    return q_text, options, ans_val

def load_old_quiz_data():
    for candidate in ['original_pdf_quiz_data.json', 'old_quiz_data.json']:
        if os.path.exists(candidate):
            for enc in ['utf-8', 'utf-8-sig', 'utf-16']:
                try:
                    with open(candidate, 'r', encoding=enc) as f:
                        return json.load(f)
                except Exception:
                    pass
    return {}

def parse_all_docx():
    old_data = load_old_quiz_data()
    all_subjects_data = {}
    
    docx_files = sorted(glob.glob('*.docx'))
    print(f"找到 {len(docx_files)} 个 Word 文件待处理:")
    for f in docx_files:
        print(f"  - {f}")
        
    stats_summary = {
        'total_questions': 0,
        'subjects': {},
        'updated_answers_total': 0,
        'brand_new_total': 0,
        'updated_questions_list': [],
        'brand_new_list': []
    }
    
    for filepath in docx_files:
        doc = docx.Document(filepath)
        subject = os.path.basename(filepath).replace('（答案+解析）.docx', '').replace('.docx', '').strip()
        paras = [p.text for p in doc.paragraphs]
        know_idxs = [i for i, p in enumerate(paras) if re.search(r'^(知识点|解析)[:：]', p.strip())]
        assert len(know_idxs) == 220, f"科目 [{subject}] 知识点数量异常: {len(know_idxs)} != 220"
        
        old_qs = old_data.get(subject, [])
        old_by_norm = {normalize_text(q['question']): q for q in old_qs if normalize_text(q.get('question'))}
        
        q_ranges = []
        
        # 确定第 1 题的起点与答案位置
        ans_p0 = None
        for p_i in range(know_idxs[0], -1, -1):
            if re.search(r'正确答案[:：]\s*[A-Da-d对错√×]', paras[p_i]):
                ans_p0 = p_i
                break
        p0 = 0
        while p0 < ans_p0 and (not paras[p0].strip() or re.search(r'^(单选题|多选题|判断题)', paras[p0]) or (paras[p0].strip().startswith('《') and paras[p0].strip().endswith('》') and len(paras[p0].strip()) < 30)):
            p0 += 1
        q_ranges.append((p0, ans_p0))
        
        # 确定后续题目的边界
        for ki in range(len(know_idxs) - 1):
            k_curr = know_idxs[ki]
            k_next = know_idxs[ki + 1]
            ans_p = None
            for p_i in range(k_next, k_curr, -1):
                if re.search(r'正确答案[:：]\s*[A-Da-d对错√×]', paras[p_i]):
                    ans_p = p_i
                    break
            assert ans_p is not None, f"科目 [{subject}] 第 {ki+2} 题未找到正确答案段落"
            
            know_end = k_curr + 1
            while know_end < ans_p:
                p_text = paras[know_end].strip()
                if not p_text:
                    next_non_empty = know_end + 1
                    while next_non_empty < ans_p and not paras[next_non_empty].strip():
                        next_non_empty += 1
                    if next_non_empty < ans_p:
                        next_t = paras[next_non_empty].strip()
                        prev_non_empty = know_end - 1
                        while prev_non_empty >= k_curr and not paras[prev_non_empty].strip():
                            prev_non_empty -= 1
                        prev_t = paras[prev_non_empty].strip() if prev_non_empty >= k_curr else ''
                        prev_ended = bool(re.search(r'[。！!？\?”’]\s*$', prev_t))
                        
                        if not prev_ended or next_t.startswith(('养）。', '政违法', '的多元化', '其他选项错误', '选项错误', '（如', '(如')):
                            know_end = next_non_empty
                            continue
                    know_end += 1
                    break
                    
                if re.search(r'^(单选题|多选题|判断题)', p_text):
                    break
                is_option_b = bool(re.search(r'(?:^|[\s\t])B[\.、]', p_text)) and not ('选项错误' in p_text or '选项都是' in p_text or re.search(r'B[、\.]\s*C[、\.]', p_text))
                if is_option_b or '正确答案' in p_text:
                    break
                    
                prev_text = paras[know_end - 1].strip()
                prev_ended = bool(re.search(r'[。！!？\?”’]\s*$', prev_text))
                is_cont = (
                    not prev_ended or
                    p_text.startswith(('（如', '(如', '（地方', '（中国', '（Quality', '（应急', '（emergency', '（即', '（内部', '（形式', '（1995', '（禁止性', '因此', '四个选项全部正确', '其他选项错误', '选项错误', '养）。', '政违法', '的多元化'))
                )
                if is_cont:
                    know_end += 1
                else:
                    break
                    
            q_start = know_end
            while q_start < ans_p and (not paras[q_start].strip() or re.search(r'^(单选题|多选题|判断题)', paras[q_start]) or (paras[q_start].strip().startswith('《') and paras[q_start].strip().endswith('》') and len(paras[q_start].strip()) < 30)):
                q_start += 1
            q_ranges.append((q_start, ans_p))
            
        subject_questions = []
        sub_updated_ans_count = 0
        sub_brand_new_count = 0
        
        for ki in range(220):
            st, ed = q_ranges[ki]
            q_num = ki + 1
            if q_num <= 160:
                type_name = '单选题'
                type_code = 'single'
                is_choice = True
            elif q_num <= 180:
                type_name = '多选题'
                type_code = 'multi'
                is_choice = True
            else:
                type_name = '判断题'
                type_code = 'judge'
                is_choice = False
                
            full_content = '\n'.join([paras[j] for j in range(st, ed + 1)])
            q_text, opts, ans_val = extract_q_and_opts(full_content, is_choice=is_choice)
            
            # 提取权威解析
            k_start = know_idxs[ki]
            next_q_start = q_ranges[ki + 1][0] if ki + 1 < 220 else len(paras)
            know_paras = [paras[j].strip() for j in range(k_start, next_q_start) if paras[j].strip()]
            know_paras = [p for p in know_paras if not re.search(r'^(单选题|多选题|判断题)', p) and not (p.startswith('《') and p.endswith('》') and len(p) < 30)]
            know_text = ' '.join(know_paras).strip()
            know_text = re.sub(r'^(知识点|解析)[:：]\s*', '', know_text).strip()
            
            # 比对旧题库：是否为新题或更新题
            is_new = False
            is_answer_updated = False
            old_ans = None
            tags = ["2026Word更新"]
            
            norm_q = normalize_text(q_text)
            matched_oq = None
            if norm_q in old_by_norm:
                matched_oq = old_by_norm[norm_q]
            else:
                for ok, oq in old_by_norm.items():
                    if len(norm_q) >= 6 and (norm_q in ok or ok in norm_q):
                        matched_oq = oq
                        break
                        
            if not matched_oq:
                is_new = True
                tags.append("全新考题")
                tags.append("重点复习")
                sub_brand_new_count += 1
                stats_summary['brand_new_list'].append({
                    'subject': subject,
                    'num': q_num,
                    'type': type_name,
                    'question': q_text,
                    'answer': ans_val,
                    'analysis': know_text
                })
            else:
                if matched_oq.get('answer') != ans_val:
                    is_answer_updated = True
                    is_new = True
                    old_ans = matched_oq.get('answer')
                    tags.append("答案订正")
                    tags.append("重点复习")
                    sub_updated_ans_count += 1
                    stats_summary['updated_questions_list'].append({
                        'subject': subject,
                        'num': q_num,
                        'type': type_name,
                        'question': q_text,
                        'new_answer': ans_val,
                        'old_answer': old_ans,
                        'analysis': know_text
                    })
                    
            q_obj = {
                'subject': subject,
                'type': type_code,
                'typeName': type_name,
                'num': q_num,
                'question': q_text,
                'options': opts,
                'answer': ans_val,
                'analysis': know_text,
                'isNew': is_new,
                'isAnswerUpdated': is_answer_updated,
                'tags': tags
            }
            if old_ans:
                q_obj['oldAnswer'] = old_ans
                
            subject_questions.append(q_obj)
            
        all_subjects_data[subject] = subject_questions
        stats_summary['subjects'][subject] = {
            'total': len(subject_questions),
            'brand_new': sub_brand_new_count,
            'updated_answers': sub_updated_ans_count
        }
        stats_summary['brand_new_total'] += sub_brand_new_count
        stats_summary['updated_answers_total'] += sub_updated_ans_count
        stats_summary['total_questions'] += len(subject_questions)
        print(f"[{subject}] 解析成功: 共 {len(subject_questions)} 题 | 全新题: {sub_brand_new_count} 题 | 答案订正: {sub_updated_ans_count} 题")

    return all_subjects_data, stats_summary

def main():
    all_data, stats = parse_all_docx()
    
    print("\n" + "="*50)
    print(f"题库全量更新统计:")
    print(f"  总题目数: {stats['total_questions']} 题")
    print(f"  全新题数: {stats['brand_new_total']} 题")
    print(f"  重点更新/答案订正题目数: {stats['updated_answers_total']} 题")
    print(f"  重点关注总题数: {stats['brand_new_total'] + stats['updated_answers_total']} 题")
    for sub, info in stats['subjects'].items():
        print(f"  - {sub}: 共 {info['total']} 题 (含 {info['brand_new']} 道新题, {info['updated_answers']} 道答案订正)")
        
    # 保存根目录 quiz_data.json
    with open('quiz_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print("\n[OK] 保存至根目录 quiz_data.json 成功!")
    
    # 同步保存至 web/quiz_data.json
    os.makedirs('web', exist_ok=True)
    with open(os.path.join('web', 'quiz_data.json'), 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print("[OK] 保存至 web/quiz_data.json 成功!")
    
    # 同步生成并保存至 web/quiz_data.js (支持 Android APK 秒开与离线运行)
    js_content = "window.DEFAULT_QUIZ_DATA = " + json.dumps(all_data, ensure_ascii=False, indent=2) + ";\n"
    with open(os.path.join('web', 'quiz_data.js'), 'w', encoding='utf-8') as f:
        f.write(js_content)
    print("[OK] 保存至 web/quiz_data.js 成功!")
    
    # 全量质量巡检校验
    print("\n" + "="*50)
    print("开始对导出的全部 1100 道题目进行质量巡检:")
    err_count = 0
    for sub, qs in all_data.items():
        for q in qs:
            q_num = q['num']
            # 题干校验
            if not q['question'] or len(q['question']) < 4:
                print(f"[ERR] [{sub}] 第 {q_num} 题题干异常: {repr(q['question'])}")
                err_count += 1
            # 答案校验
            if not q['answer']:
                print(f"[ERR] [{sub}] 第 {q_num} 题无答案!")
                err_count += 1
            # 选择题校验
            if q['type'] in ['single', 'multi']:
                for opt_k in ['A', 'B', 'C', 'D']:
                    if not q['options'].get(opt_k):
                        print(f"[ERR] [{sub}] 第 {q_num} 题缺失选项 {opt_k}: options={q['options']}")
                        err_count += 1
                if q['type'] == 'single' and len(q['answer']) != 1:
                    print(f"[ERR] [{sub}] 单选第 {q_num} 题答案长度异常: {q['answer']}")
                    err_count += 1
                if q['type'] == 'multi' and len(q['answer']) < 2:
                    print(f"[WARN] [{sub}] 多选第 {q_num} 题答案长度仅为 {q['answer']}")
            elif q['type'] == 'judge':
                if q['answer'] not in ['对', '错']:
                    print(f"[ERR] [{sub}] 判断题第 {q_num} 题答案异常: {q['answer']}")
                    err_count += 1
            # 解析校验
            if not q['analysis']:
                print(f"[WARN] [{sub}] 第 {q_num} 题无权威解析!")
    if err_count == 0:
        print(">>> 巡检完成: 全部 1100 道题 100% 完美无任何错误！<<<")
    else:
        print(f">>> 巡检完成: 发现 {err_count} 处错误! <<<")

if __name__ == '__main__':
    main()
