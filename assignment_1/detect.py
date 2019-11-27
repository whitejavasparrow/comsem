# -*- coding: utf-8 -*-
import csv
import re
import time
import datetime
from datetime import datetime
from workalendar.asia import Taiwan
from opencc import OpenCC
import os
import dateparser
import pandas as pd
import numpy as np
import sys

#input_path = sys.argv[0]
#input_all = open(input_path, 'r', encoding = 'utf-8')
#sentences, date_lst, time_lst = input_all.split("\n")

sentences = "即使今年 iPhone 11 系列才剛推出，但目前下一代 iPhone 的傳聞已經謠言滿天飛了，隨著目前 iPhone 11 搭配 iOS 13 有不少 Bug 的同時，Apple 也加快腳步，研發下一代的 iPhone。海外媒體報導，下一代 iPhone 12 將可能出廠搭載 6GB 的RAM，同時小手機 iPhone SE 2 也傳聞將在明年二月推出。\n由於目前 iOS 13 問題多多，而眾多問題都被指向 iPhone 的記憶體太小，無法正常管理眾多應用程式，現在已有海外分析師透漏來自 Apple 供應鏈的情報，下一代的 iPhone 12 Pro 以及 iPhone 12 Pro MAX 將會捨棄 4GB 的RAM，直接擁抱 6GB RAM 的規格，避免 iOS 14 的慘案再度出現。\n另外則是謠傳已久的 iPhone SE 2 據傳目前已經進入最後階段，估計將在明年 2 月會開始生產 iPhone SE 2，，這款手機將會搭配 4.7 吋小螢幕以及 Touch ID，外觀接近 iPhone 8 的設計，最快大概明年三月就能看到 iPhone SE 2 的上市。"
date_lst = ['明年二月', '明年三月']
time_lst = []

# translate simplified chinese into traditional chinese
def translate(source_file, result_file):
    cc = OpenCC('s2t')
    source = open(source_file, 'r', encoding = 'utf-8')
    result = open(result_file, 'w', encoding = 'utf-8')
    # source放純文字檔，轉完放result
    count = 0
    while True:
        line = source.readline()
        line = cc.convert(line)
        if not line:  #readline會一直讀下去
            break
        print(line)
        count = count +1
        result.write(line) 
        print('===已處理'+str(count)+'行===')
    source.close()        
    result.close()

for root, dirs, files in os.walk("chinese"):
    for file in files:
        if file.endswith(".txt"):
            file_path = os.path.join(root, file)
            translate(file_path, os.path.join("chinese_traditional", file))       

# prepare text to be evaluated
sentence_lst = sentences.split("\n")

results = []
results = results + [{"source": n, "target": ""} for n in date_lst] + [{"source": n, "target": ""} for n in time_lst]

for n in date_lst:
    try:
        target = dateparser.parse(n)
        if not target == None:
            results.append({"source": n, "target": target})
    except:
        pass

for n in time_lst:
    try:
        target = dateparser.parse(n)
        if not target == None:
            results.append({"source": n, "target": target})
    except:
        pass
    
# find target using resources from HeidelTime

repattern_lst, rules_lst, normalization_lst = [], [], []
for root, dirs, files in os.walk("chinese_traditional_edited"):
    for file in files:
        if file.endswith(".txt"):
            file_path = os.path.join(root, file)
            txt = open(file_path, 'r', encoding = 'utf-8').read()
            if "repattern" in file:
                repattern_lst.append({"filename": file, "content": txt})
            elif "rules" in file:
                rules_lst.append({"filename": file, "content": txt})
            elif "normalization" in file:
                normalization_lst.append({"filename": file, "content": txt})

repattern_dic = []

for n in repattern_lst:
    tag = re.match(r"(re.*|tense.*)\.txt", n["filename"].split("_")[-1]).group(1)
    content_lst = n["content"].split("\n")
    repattern = [content for content in content_lst if "//" not in content and content != ""]
    
    repattern_dic.append({"tag": tag, "repattern": repattern})

rules_dic = []

for n in rules_lst:
    lines = n["content"].split("\n")
    lines = [line.replace("// ", "") for line in lines if "RULENAME" in line]

    for line in lines[1:]:
        rules_params = line.split(",")
        try:
            param_dic = {}
            for param in rules_params:
                tag, rule = param.split("=")
                param_dic[tag] = rule.replace('"', '').replace('“', '').replace('”', '')
                rules_dic.append(param_dic)
        except:
            print("---")
            print(param)
            print(n["filename"])
            
def match_EXTRACTION(extraction):
    for n in repattern_dic:
        if n["tag"] in extraction:
            #print("---")
            #print(n["tag"])
            #print(n["repattern"])
            regex = '|'.join(n["repattern"])
            extraction = extraction.replace("%"+n["tag"], "("+regex+")")
    return extraction

matched_rules_dic = []
for i, rule in enumerate(rules_dic):
    matched_EXTRACTION = match_EXTRACTION(rule["EXTRACTION"])
    rule_dic = rules_dic[i]
    rule_dic["matched_EXTRACTION"] = matched_EXTRACTION
    matched_rules_dic.append(rule_dic)

def HeidelTime_detect(string):
    found = []
    for i, rule in enumerate(matched_rules_dic):
        try:
            attempt = re.match(rule["matched_EXTRACTION"], string)
            if attempt.group(0) in found:
                pass
            else:
                found.append(attempt.group(0))
        except:
            pass
    return found

for sentence in sentence_lst:
    sources = HeidelTime_detect(sentence)
    if sources != []:
        for source in sources:
            results.append({"source": source, "target": ""})

results

df = pd.DataFrame(results)
df = df.replace("", np.nan, regex=True)
df = df.groupby("source").first().reset_index()
df.index = df.index + 1

print(df)