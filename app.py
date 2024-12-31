#T11s 111550092 韓承芳

from pytrends.request import TrendReq
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/trend', methods=['POST'])
def google_trend_explorer():
    data = request.get_json()
    keyword = data.get('keyword')
    region = data.get('region')

    if not keyword:
        return jsonify({"error": "請提供關鍵字"}), 400

    try:
        pytrend = TrendReq(timeout=(10,25))
        pytrend.build_payload(kw_list=[keyword], cat=0, timeframe='today 1-m', geo=region)
        data = pytrend.interest_over_time()
        data = data.drop(columns=["isPartial"])
        suggestions = pytrend.suggestions(keyword)
        kw_list = [s['mid'] for s in suggestions]
        title_list = [s['title'] for s in suggestions]
        type_list = [s['type'] for s in suggestions]
        batch_size = 1
        batches = [kw_list[i:i + batch_size] for i in range(0, len(kw_list), batch_size)]

        all_data = []

        for batch in batches:
            print(f"處理關鍵字: {batch}")
            pytrend.build_payload(batch, cat=0, timeframe='today 1-m', geo='US')
            batch_data = pytrend.interest_over_time()
            if not batch_data.empty:
                if "isPartial" in batch_data.columns:
                    batch_data = batch_data.drop(columns=["isPartial"])
                all_data.append(batch_data)

        if all_data:
            combined_data = pd.concat(all_data, axis=1)
        else:
            print("未獲得任何資料。")

        if not combined_data.empty:
            new_columns = {}
            for col in combined_data.columns:
                if col in kw_list:
                    index = kw_list.index(col)
                    new_columns[col] = f"{title_list[index]}\n({type_list[index]})"
            combined_data.rename(columns=new_columns, inplace=True)
        if not data.empty and not combined_data.empty:
            combined_data = pd.concat([data, combined_data], axis=1)
        else:
            combined_data = data if not data.empty else combined_data
        if not combined_data.empty:
            combined_data.to_csv('static/trend_combined.csv', index=True)
            print("資料已成功儲存到 'static/trend_combined.csv'")
            return jsonify({"message": "Success！Going to Refresh!", "refresh": True})
        else:
            return jsonify({"message": "未取得任何資料，請檢查關鍵字或其他參數。"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)