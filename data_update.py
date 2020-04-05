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


### 患者数の取得 ###
res = requests.get("https://www.pref.yamaguchi.lg.jp/cms/a15200/kansensyou/koronahassei.html")
res.encoding = res.apparent_encoding	# 日本語文字化け対応
soup2 = BeautifulSoup(res.content, "html.parser")
search2 = re.compile("\d{1,3}例")
pat_num = soup2.find_all("h2", text=search2)[0].string
pat_num = int(re.sub("\\D", "", pat_num[:3]))


# 各更新項目の既知データをtemplateから取得
patients_summary = template['patients_summary']['data']
inspection_summary = template['inspections_summary']['data']
quarents = template['querents']['data']

pat_list = [p["小計"] for p in patients_summary]
pat_numago = sum(pat_list)
pat_ldate = datetime.datetime.strptime(patients_summary[-1]["日付"][:10], '%Y-%m-%d')	# 各データの更新日
pat_ldate = datetime.date(pat_ldate.year, pat_ldate.month, pat_ldate.day)
if pat_ldate == yesterday_datetime:	# 昨日のログがあれば
	print("患者の今日のログあり")
	pat_numago -= patients_summary[-1]["小計"]
pat_num -= pat_numago

# データの更新
inspection_summary = check_update(inspection_summary, ins_num, yesterday_datetime, yesterday)
quarents = check_update(quarents, qua_num, yesterday_datetime, yesterday)
patients_summary = check_update(patients_summary, pat_num, yesterday_datetime, yesterday)

print("="*10)
print("最終更新日： " + str(last_update_date))
#print("患者数: " + str(pat_num))
print("検査件数: " + str(qua_num))
print("相談件数: " + str(ins_num))
print("="*10)


# 出力用jsonデータの構築
template["lastUpdate"] = last_update_date
template['inspections_summary']['date'] = last_update_date
template['inspections_summary']['data'] = inspection_summary
template['querents']['date'] = last_update_date
template['querents']['data'] = quarents
template['patients_summary']['date'] = last_update_date
#template['patients_summary']['data'] = patients_summary
template['patients']['date'] = last_update_date

# jsonファイルに出力
export_json(obj=template, filename="./data/data.json")