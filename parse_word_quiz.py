import docx
import glob
import os
import re
import json

def clean_txt(s):
    if not s:
        return ''
    s = s.replace('\u3000', ' ').replace('\xa0', ' ').replace('\t', ' ')
    s = re.sub(r' +', ' ', s)
    return s.strip()

def normalize_text(s):
    if not s:
        return ''
    return re.sub(r'[\s_—\t\r\n\.,，。、“”\"\'：:\(\)（）\?？]+', '', s).strip()

def load_old_quiz_data():
    if os.path.exists('original_pdf_quiz_data.json'):
        with open('original_pdf_quiz_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    elif os.path.exists('old_quiz_data.json'):
        with open('old_quiz_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    elif os.path.exists('quiz_data.json'):
        with open('quiz_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def parse_all_docx():
    old_data = load_old_quiz_data()
    all_subjects_data = {}
    
    docx_files = sorted(glob.glob('*.docx'))
    print(f"找到 {len(docx_files)} 个 Word 文件待导入:")
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
        paras = [clean_txt(p.text) for p in doc.paragraphs if clean_txt(p.text)]
        
        know_indices = [i for i, p in enumerate(paras) if re.match(r'^(知识点|解析)[:：]', p)]
        assert len(know_indices) == 220, f"{subject} 知识点段落数异常: {len(know_indices)}"
        
        old_qs = old_data.get(subject, [])
        old_by_norm = {normalize_text(q['question']): q for q in old_qs if normalize_text(q.get('question'))}
        
        # 1. 确定每题的段落边界 [q_start, q_end]
        q_ranges = []
        p0 = 0
        while p0 < know_indices[0] and (re.search(r'(单选题|多选题|判断题)\s*(?:（?共|\d+题)', paras[p0]) or (paras[p0].startswith('《') and paras[p0].endswith('》'))):
            p0 += 1
        q_ranges.append((p0, know_indices[0]))
        
        for ki in range(len(know_indices) - 1):
            k_curr = know_indices[ki]
            k_next = know_indices[ki + 1]
            
            ans_idx = -1
            for j in range(k_next - 1, k_curr, -1):
                if '正确答案' in paras[j]:
                    ans_idx = j
                    break
            assert ans_idx != -1, f"{subject} 第 {ki+2} 题未找到正确答案段落"
            
            know_end = k_curr + 1
            while know_end < ans_idx:
                p_prev = paras[know_end - 1]
                p_this = paras[know_end]
                if re.search(r'(单选题|多选题|判断题)\s*(?:（?共|\d+题)', p_this):
                    break
                if re.search(r'^[A-D][\.、\s]', p_this) or re.search(r'(?:^|\s+)[A-D][\.、\s]', p_this):
                    break
                    
                prev_ended = p_prev.endswith(('。', '！', '”', '’'))
                is_know_continuation = (
                    not prev_ended or
                    p_this.startswith(('①', '②', '③', '④', '⑤', '（', '(', '1.', '2.', '3.')) or
                    p_this.startswith(('A选项', 'B选项', 'C选项', 'D选项', '选项A', '选项B', '选项C', '选项D'))
                )
                if prev_ended and not is_know_continuation and (ans_idx - know_end <= 3):
                    break
                know_end += 1
                
            q_start = know_end
            while q_start < k_next and (re.search(r'(单选题|多选题|判断题)\s*(?:（?共|\d+题)', paras[q_start]) or (paras[q_start].startswith('《') and paras[q_start].endswith('》'))):
                q_start += 1
                
            q_ranges.append((q_start, k_next))
            
        subject_questions = []
        sub_updated_ans_count = 0
        sub_brand_new_count = 0
        
        for ki in range(220):
            q_start, q_end = q_ranges[ki]
            k_start = know_indices[ki]
            
            next_q_start = q_ranges[ki + 1][0] if ki + 1 < 220 else len(paras)
            know_paras = paras[k_start:next_q_start]
            know_paras = [p for p in know_paras if not re.search(r'(单选题|多选题|判断题)\s*(?:（?共|\d+题)', p) and not (p.startswith('《') and p.endswith('》'))]
            know_text = ' '.join(know_paras).strip()
            know_text = re.sub(r'^(知识点|解析)[:：]\s*', '', know_text).strip()
            
            q_paras = paras[q_start:k_start]
            q_paras = [p for p in q_paras if not re.search(r'(单选题|多选题|判断题)\s*(?:（?共|\d+题)', p) and not (p.startswith('《') and p.endswith('》'))]
            
            q_num = ki + 1
            if q_num <= 160:
                type_name = '单选题'
                type_code = 'single'
            elif q_num <= 180:
                type_name = '多选题'
                type_code = 'multi'
            else:
                type_name = '判断题'
                type_code = 'judge'
                
            full_q_str = ' '.join(q_paras).strip()
            ans_m = re.search(r'正确答案[:：]\s*([A-Za-z对错√×ABCD]+)', full_q_str)
            ans_val = ''
            if ans_m:
                ans_val = ans_m.group(1).strip()
                if ans_val in ['√', '对', '正确']:
                    ans_val = '对'
                elif ans_val in ['×', '错', '错误']:
                    ans_val = '错'
                q_without_ans = (full_q_str[:ans_m.start()] + ' ' + full_q_str[ans_m.end():]).strip()
            else:
                q_without_ans = full_q_str
                
            if type_code == 'judge':
                q_text = q_without_ans.strip()
                options = {}
            else:
                opt_matches = list(re.finditer(r'(?:^|\s+)([A-D])[\.、\s]\s*', q_without_ans))
                options = {}
                if opt_matches and len(opt_matches) >= 2:
                    q_text = q_without_ans[:opt_matches[0].start()].strip()
                    for oi, om in enumerate(opt_matches):
                        opt_k = om.group(1)
                        st = om.end()
                        ed = opt_matches[oi+1].start() if oi + 1 < len(opt_matches) else len(q_without_ans)
                        options[opt_k] = q_without_ans[st:ed].strip()
                else:
                    b_m = re.search(r'(?:^|\s+)B[\.、\s]\s*', q_without_ans)
                    if b_m:
                        part_before_b = q_without_ans[:b_m.start()].strip()
                        q_text = part_before_b
                    else:
                        q_text = q_without_ans.strip()
            
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
                'options': options,
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
    
    # 输出详细的新题与更新题清单报告
    print("\n" + "="*50)
    print("【重点更新/答案订正题目清单 - 复习着重关注】:")
    for item in stats['updated_questions_list']:
        print(f"• [{item['subject']}] 第 {item['num']} 题 ({item['type']})")
        print(f"   题干: {item['question']}")
        print(f"   最新Word答案: 【{item['new_answer']}】  (旧版错误答案: {item['old_answer']})")
        print(f"   权威解析: {item['analysis'][:80]}...")
        print()
        
    print("\n" + "="*50)
    print("【全新考题清单 - 复习着重关注】:")
    for item in stats['brand_new_list']:
        print(f"• [{item['subject']}] 第 {item['num']} 题 ({item['type']})")
        print(f"   题干: {item['question']}")
        print(f"   答案: 【{item['answer']}】")
        print(f"   权威解析: {item['analysis'][:80]}...")
        print()

if __name__ == '__main__':
    main()
