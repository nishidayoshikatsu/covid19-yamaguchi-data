import requests
import re
import datetime
from bs4 import BeautifulSoup
import jaconv
import json
import sys

YEAR = 2020 #現状は2020年で決め打ち
DAYS_OF_WEEK = ["月","火","水","木","金","土","日"]

# import json(template)
def import_json(filename):
    with open(filename, "r") as f:
        dict = json.load(f)
        return dict
    
# export json
def export_json(obj, filename):
    with open(filename, "w") as f:
        json.dump(
            obj=obj,
            fp=f,
            ensure_ascii=False,
            indent=4,
            sort_keys=False,
            separators=None
            )

def get_patients(s): # 陽性数を返す
    search = re.compile("^(?=.*結果：陰性).*$")
    inspections_element = s.find("p", text=search) # 変数searchで指定する正規表現に一致するpタグを取り出す

    inspections = re.findall(r'[0-9]+', jaconv.z2h(inspections_element.text.replace("，", ""), kana=False, digit=True, ascii=True))  # 対象のpタグから数値を取り出す

    patients_num = int(inspections[2])  if len(inspections) > 2 else 0 #県のサイトでは陽性が出ていないときは陰性の数しか書かれていないため
    
    return patients_num

def get_inspections(s): # PCR検査数を返す
    search = re.compile("^(?=.*PCR検査した検体総数).*$")
    pcr_inspections_element = s.find("p", text=search) # 変数searchで指定する正規表現に一致するpタグを取り出す

    pcr_inspections = re.findall(r'[0-9]+', jaconv.z2h(pcr_inspections_element.text.replace("，", ""), kana=False, digit=True, ascii=True))  # 対象のpタグから数値を取り出す

    pcr_inspection_num = int(pcr_inspections[0])
    
    return pcr_inspection_num

def get_quarents(s): # 相談件数を返す
    search = re.compile("^(全県相談件数：).*$")
    quarents_element = s.find("p", text=search) # 変数searchで指定する正規表現に一致するpタグを取り出す

    quarents = re.findall(r'[0-9]+', jaconv.z2h(quarents_element.text.replace("，", ""), kana=False, digit=True, ascii=True))  # 対象のpタグから数値を取り出す

    quarents_num = int(quarents[0])

    return quarents_num

def get_timestamp(s): # その記事内のタイムスタンプを返す、現在は未使用
    search = re.compile("^(?=.*までの件数は次のとおりです).*$")
    date_element = s.find("p", text=search)

    date = re.findall(r'[0-9]+', jaconv.z2h(date_element.text.replace("，", ""), kana=False, digit=True, ascii=True)) # 対象のpタグから数値を取り出す

    time_stamp = "{}-{}-{}T08:00:00.000Z".format(YEAR, date[0].zfill(2), date[1].zfill(2)) # 現状は8時決め打ちで、json記載のタイムスタンプに整形している
    
    return time_stamp

# 現在のdata.jsonをバックアップしてdata_template.jsonに保存する
template = import_json("./data/data.json")
export_json(obj=template, filename="./data/data_template.json")

# 報道発表ページで「新型コロナウイルス感染症にかかる」で検索した際の結果を利用
res = requests.get("https://www.pref.yamaguchi.lg.jp/cms/a15200/kansensyou/ncorona.html")
res.encoding = res.apparent_encoding
soup = BeautifulSoup(res.content, "html.parser")

# 更新日の取得
last_update_date = "{0:%Y/%m/%d %H:%M}".format(datetime.datetime.now())

search = re.compile("^.*$")
update = soup.find_all("span", text=search)[0].string

date_pattern = re.compile(r"[0-9]{1,4}")
web_date = re.findall(date_pattern, update)
web_date = list(map(int, web_date))

if not web_date:	# 日付データがとれなければ終了
    sys.exit()

print("正規表現")
print(last_update_date)
print(update)
print(web_date[1:])

web_date = datetime.date(web_date[1], web_date[2], web_date[3])
print(web_date)


# 検査件数の取得
search = re.compile("^(?=.*PCR検査した検体総数).*$")
ins_num = soup.find_all("p", text=search)[0].string
ins_num = re.sub("\\D", "", ins_num)

# 各更新項目の既知データをtemplateから取得
patients_summary = template['patients_summary']['data']
inspection_summary = template['inspections_summary']['data']
quarents = template['querents']['data']


yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
t_stamp = '{0:%Y-%m-%d}'.format(yesterday)
print(yesterday)

#inspection_summary.append({
#    "日付": t_stamp + "T08:00:00.000Z",
#    "小計": ins_num
#})

"""
print(elem.attrs['href'])
res = requests.get(elem.attrs['href'])
res.encoding = res.apparent_encoding 
soup = BeautifulSoup(res.content, "html.parser")

pat_num = get_patients(soup)
ins_num = get_inspections(soup)
qua_num = get_quarents(soup)

yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
t_stamp = '{0:%Y-%m-%d}'.format(yesterday)

# これまでの陽性者の合計を求める
total_patients_num = 0
for patient in template['patients_summary']['data']:
   total_patients_num += patient['小計']

# 今日の陽性者数を求める
today_pat_num = pat_num - total_patients_num

# 各項目に更新内容を追加
patients_summary.append({
    "日付": t_stamp + "T08:00:00.000Z",
    "小計": today_pat_num
})

inspection_summary.append({
    "日付": t_stamp + "T08:00:00.000Z",
    "小計": ins_num
})

quarents.append({
    "日付": t_stamp + "T08:00:00.000Z",
    "曜日": DAYS_OF_WEEK[yesterday.weekday()],
    "9-17時": 1688,
    "17-翌9時": 130,
    "date": t_stamp,
    "w": 2,
    "short_date": t_stamp[5:7]+ "/" + t_stamp[8:10] ,
    "小計": qua_num
})

last_update_date = "{0:%Y/%m/%d 8:00}".format(datetime.datetime.now())

print("陽性数 ： ", get_patients(soup))
print("PCR検査数 ： ", get_inspections(soup))
print("相談件数 ： ", get_quarents(soup))
print("記事のタイムスタンプ ： ", get_timestamp(soup))

# 出力用jsonデータの構築
template["lastUpdate"] = last_update_date
template['querents']['date'] = last_update_date
template['querents']['data'] = quarents
template['patients_summary']['date'] = last_update_date
template['patients_summary']['data'] = patients_summary
template['inspections_summary']['date'] = last_update_date
template['inspections_summary']['data'] = inspection_summary

# jsonファイルに出力
export_json(obj=template, filename="./data/data.json")
"""