import requests
import re
import datetime
from bs4 import BeautifulSoup
import jaconv
import json
import sys

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

def check_update(jsondata, content, yesterday_datetime, yesterday):
	log_date = datetime.datetime.strptime(jsondata[-1]["日付"][:10], '%Y-%m-%d')	# 各データの更新日
	log_date = datetime.date(log_date.year, log_date.month, log_date.day)

	if log_date == yesterday_datetime:	# 昨日のログがある場合
		print("昨日のログは記入済み")
		if content != int(jsondata[-1]["小計"]):	# 昨日のログの数字と最新データの数字が異なる場合
			print("新しいデータを更新")
			jsondata[-1]["小計"] = content	# 上書き
		else:
			print("データは更新済みです")
	else:	# 昨日のログがない場合（）
		print("昨日のログを記入します")
		jsondata.append({
			"日付": yesterday + "T08:00:00.000Z",
			"小計": int(jsondata[-1]["小計"])
		})

	return jsondata

# 現在のdata.jsonをバックアップしてdata_template.jsonに保存する
template = import_json("./data/data.json")
export_json(obj=template, filename="./data/data_template.json")

# タイムゾーンの生成
JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')

# 報道発表ページで「新型コロナウイルス感染症にかかる」で検索した際の結果を利用
res = requests.get("https://www.pref.yamaguchi.lg.jp/cms/a15200/kansensyou/ncorona.html")
res.encoding = res.apparent_encoding	# 日本語文字化け対応
soup = BeautifulSoup(res.content, "html.parser")

### 更新日の取得 ###
#search = re.compile("^.*$")
#update = soup.find_all("span", text=search)[0].string	# 更新日の範囲を取得

date_pattern = re.compile(r"[0-9]{1,4}")
#web_date = re.findall(date_pattern, update)
#web_date = list(map(int, web_date))

#if not web_date:	# 日付データがとれなければ終了
#    sys.exit()

#web_date = datetime.date(web_date[1], web_date[2], web_date[3])

#update_date = datetime.date.today() - web_date
yesterday_datetime = datetime.date.today() - datetime.timedelta(days=1)
yesterday = '{0:%Y-%m-%d}'.format(yesterday_datetime)

### 最終更新日の取得 ###
last_update_date = "{0:%Y/%m/%d %H:%M}".format(datetime.datetime.now(JST))
print("最終更新日： " + str(last_update_date))

### 検査件数の取得 ###
search = re.compile("^(?=.*PCR検査した検体総数).*$")
ins_num = soup.find_all("p", text=search)[0].string
ins_num = int(re.sub("\\D", "", ins_num))
# 検査件数の集計日を取得
#search = re.compile("^.*○県内のPCR検査実施件数.*$")
#ins_day = soup.find_all("p", text=search)[0].string
#date_pattern = re.compile(r"\d{1,4}")
#ins_day = re.findall(date_pattern, ins_day)
#ins_day = list(map(int, ins_day))
#ins_day = datetime.date(2018+ins_day[0], ins_day[1], ins_day[2])

### 相談件数の取得 ###
search = re.compile("^.*全県相談件数.*$")
qua_num = soup.find_all("p", text=search)[0].string
qua_num = int(re.sub("\\D", "", qua_num))

# 各更新項目の既知データをtemplateから取得
patients_summary = template['patients_summary']['data']
inspection_summary = template['inspections_summary']['data']
quarents = template['querents']['data']

# データの更新
inspection_summary = check_update(inspection_summary, ins_num, yesterday_datetime, yesterday)
quarents = check_update(quarents, qua_num, yesterday_datetime, yesterday)

# 出力用jsonデータの構築
template["lastUpdate"] = last_update_date
template['inspections_summary']['date'] = last_update_date
template['inspections_summary']['data'] = inspection_summary
template['querents']['date'] = last_update_date
template['querents']['data'] = quarents

# jsonファイルに出力
export_json(obj=template, filename="./data/data.json")

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