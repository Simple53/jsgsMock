import pymupdf
import glob
import re
import json
import os

def clean_text(text):
    # 统一空白字符与换行
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # 替换中文全角空格等
    text = text.replace('\u3000', ' ').replace('\xa0', ' ')
    return text

def parse_pdf_file(filepath):
    subject = os.path.basename(filepath).replace("（答案+解析）.pdf", "").replace(".pdf", "").strip()
    doc = pymupdf.open(filepath)
    full_text = ""
    for page in doc:
        full_text += clean_text(page.get_text()) + "\n"
    doc.close()

    # 识别三大题型的起始位置
    # 单选题、多选题、判断题
    type_matches = list(re.finditer(r'(?:^|\n)\s*(?:《[^》]+》\s*)?(单选题|多选题|判断题)[^\n]*', full_text))
    sections = []
    for i, m in enumerate(type_matches):
        q_type = m.group(1)
        start_idx = m.end()
        end_idx = type_matches[i+1].start() if i + 1 < len(type_matches) else len(full_text)
        sections.append((q_type, full_text[start_idx:end_idx]))

    questions = []
    for q_type, sec_text in sections:
        # 分割题目：按行首数字编号，如 "1. "、"2. " 等
        # 注意不要把解析内部的数字分割掉，所以按 "\n\s*(\d+)[\.、\s]" 匹配
        q_blocks = re.split(r'(?:^|\n)\s*(\d+)[\.、\s]\s*', sec_text)
        # q_blocks[0] 是题目前面的说明文字，后面按 [num, content, num, content...]
        if len(q_blocks) <= 1:
            continue

        for k in range(1, len(q_blocks), 2):
            q_num = int(q_blocks[k])
            raw_content = q_blocks[k+1]

            # 提取 正确答案 和 知识点/解析
            ans_match = re.search(r'正确答案[:：]\s*([A-Za-z对错√×ABCD]+)', raw_content)
            if not ans_match:
                continue

            ans_val = ans_match.group(1).strip()
            # 规范化判断题答案
            if ans_val in ['√', '对', '正确']:
                ans_val = '对'
            elif ans_val in ['×', '错', '错误']:
                ans_val = '错'

            pre_ans = raw_content[:ans_match.start()].strip()
            post_ans = raw_content[ans_match.end():].strip()

            # 解析部分
            analysis = ""
            analysis_match = re.search(r'(?:知识点|解析)[:：]\s*(.*)', post_ans, re.DOTALL)
            if analysis_match:
                analysis = analysis_match.group(1).strip()
                # 去掉页面多余的页眉页脚页码（比如中间夹杂的纯数字行或科目名）
                analysis = re.sub(r'\n\s*\d+\s*\n', '\n', analysis)
                analysis = re.sub(r'\s+', ' ', analysis).strip()

            # 处理题干和选项
            if q_type == "判断题":
                q_text = pre_ans
                q_text = re.sub(r'\s+', ' ', q_text).strip()
                options = {}
                type_code = "judge"
            else:
                type_code = "single" if q_type == "单选题" else "multi"
                # 提取选项 A/B/C/D
                # 寻找 A. 或 A、 或 A 等
                opt_matches = list(re.finditer(r'(?:^|\s+)([A-D])[\.、\s]\s*', pre_ans))
                if opt_matches:
                    q_text = pre_ans[:opt_matches[0].start()].strip()
                    q_text = re.sub(r'\s+', ' ', q_text).strip()
                    options = {}
                    for oi, om in enumerate(opt_matches):
                        opt_key = om.group(1)
                        opt_start = om.end()
                        opt_end = opt_matches[oi+1].start() if oi + 1 < len(opt_matches) else len(pre_ans)
                        opt_val = pre_ans[opt_start:opt_end].strip()
                        # 去掉换行
                        opt_val = re.sub(r'\s+', ' ', opt_val).strip()
                        options[opt_key] = opt_val
                else:
                    q_text = re.sub(r'\s+', ' ', pre_ans).strip()
                    options = {}

            questions.append({
                "subject": subject,
                "type": type_code,
                "typeName": q_type,
                "num": q_num,
                "question": q_text,
                "options": options,
                "answer": ans_val,
                "analysis": analysis
            })
            
    return questions

def main():
    pdf_files = sorted(glob.glob("*.pdf"))
    all_data = {}
    total_count = 0

    for f in pdf_files:
        qs = parse_pdf_file(f)
        sub_name = os.path.basename(f).replace("（答案+解析）.pdf", "").replace(".pdf", "").strip()
        all_data[sub_name] = qs
        total_count += len(qs)
        print(f"Subject '{sub_name}': extracted {len(qs)} questions.")

    print("=" * 40)
    print(f"Total extracted across all subjects: {total_count}")

    # 保存完整的 JSON
    with open("quiz_data.json", "w", encoding="utf-8") as out:
        json.dump(all_data, out, ensure_ascii=False, indent=2)
    print("Saved to quiz_data.json successfully!")

    # 同步保存到 web/quiz_data.json 与 web/quiz_data.js (支持 APK 离线秒开)
    os.makedirs("web", exist_ok=True)
    with open(os.path.join("web", "quiz_data.json"), "w", encoding="utf-8") as out:
        json.dump(all_data, out, ensure_ascii=False, indent=2)
    with open(os.path.join("web", "quiz_data.js"), "w", encoding="utf-8") as out:
        out.write("window.DEFAULT_QUIZ_DATA = " + json.dumps(all_data, ensure_ascii=False, indent=2) + ";\n")
    print("Saved to web/quiz_data.json and web/quiz_data.js successfully!")

if __name__ == "__main__":
    main()
