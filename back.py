import json
import math
import os
import shutil
import sqlite3
import traceback

from flask import Flask, jsonify, make_response, request
from flask_cors import CORS

from place_Helper import get_nearby_places
from run_decet import detect_labels


def copy_ultralytics_settings():
    source = os.path.join(os.path.dirname(__file__), 'config', 'settings.json')
    target_dir = os.path.expanduser('~/.config/Ultralytics')
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, 'settings.json')

    if not os.path.exists(target):
        shutil.copy(source, target)
        print("✅ 已將本地設定檔複製到 Ultralytics 設定資料夾")
    else:
        print("🔁 Ultralytics 設定檔已存在，略過複製")


copy_ultralytics_settings()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


def clean_data(data):
    """
    遞迴清理資料中所有字串的開頭空格
    """
    if isinstance(data, dict):
        return {key: clean_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_data(item) for item in data]
    elif isinstance(data, str):
        return data.lstrip()  # 去除開頭的空格
    else:
        return data


def copy_ultralytics_settings():
    source = os.path.join(os.path.dirname(__file__), 'config', 'settings.json')
    target_dir = os.path.expanduser('~/.config/Ultralytics')
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, 'settings.json')

    if not os.path.exists(target):
        shutil.copy(source, target)
        print("✅ 已將本地設定檔複製到 Ultralytics 設定資料夾")
    else:
        print("🔁 Ultralytics 設定檔已存在，略過複製")


# 計算兩點之間的距離（哈弗賽公式）
def calculate_distance(lat1, lon1, lat2, lon2):
    try:
        # 轉換為浮點數
        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)

        # 將經緯度轉換為弧度
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(lat2)
        lon2 = math.radians(lon2)

        # 哈弗賽公式
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # 地球平均半徑，單位公里
        return c * r
    except Exception as e:
        print(f"計算距離時發生錯誤: {e}")
        return float('inf')  # 返回無窮大表示計算失敗


@app.route('/detect', methods=['POST'])
def detect():
    try:
        # 檢查是否有檔案上傳
        if 'image' not in request.files:
            return jsonify({'error': '沒有上傳圖片'})

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '未選擇檔案'})

        # 確保目錄存在
        import os

        temp_path = 'temp.jpg'

        # 儲存檔案
        file.save(temp_path)

        # 檢查檔案是否成功儲存
        if not os.path.exists(temp_path):
            return jsonify({'error': '檔案儲存失敗'})

        # 辨識標籤
        try:
            label_name = detect_labels(temp_path)
            if not label_name:
                return jsonify({'error': '無法辨識圖片內容'})
        except Exception as e:
            traceback.print_exc()
            return jsonify({'error': f'辨識圖片時發生錯誤: {str(e)}'})

        print('辨識到的 label_name:', label_name)

        # 資料庫查詢
        try:
            con = sqlite3.connect('buildings.db')
            cur = con.cursor()

            # 查詢建築物資訊
            cur.execute("SELECT * FROM buildings WHERE label_name = ?", (label_name,))
            building = cur.fetchone()

            if not building:
                return jsonify({'error': '未找到辨識到的建築物'})

            building_lat = building[13]  # 更新為新結構中 lat 的索引
            building_lng = building[14]  # 更新為新結構中 lng 的索引

            # 查詢所有景點資料
            nearby_places = []
            try:
                # 獲取所有景點資料
                cur.execute("SELECT * FROM places")
                all_places = cur.fetchall()

                if all_places:
                    # 計算每個景點與建築物的距離
                    for place in all_places:
                        # places 表結構: id, name, eng_name, address, eng_address, type, eng_type, info, eng_info, lat, lng
                        place_lat = place[11]  # lat 是第10個欄位 (索引9)
                        place_lng = place[12]  # lng 是第11個欄位 (索引10)

                        # 計算距離
                        distance = calculate_distance(
                            building_lat, building_lng, place_lat, place_lng
                        )

                        # 僅選擇距離在 5 公里內的景點
                        if distance <= 5:
                            nearby_places.append(
                                {
                                    'name': place[1],  # name
                                    'eng_name': place[2],  # eng_name
                                    'dis': place[3],  # dis
                                    'eng_dis': place[4],  # eng_dis
                                    'address': place[5],  # address
                                    'eng_address': place[6],  # eng_address
                                    'type': place[7],  # type
                                    'eng_type': place[8],  # eng_type
                                    'info': place[9],  # info
                                    'eng_info': place[10],  # eng_info
                                    'lat': place[11],  # lat
                                    'lng': place[12],  # lng
                                    'distance': round(distance, 2),
                                    'is_building': False,
                                }
                            )

                # 根據距離排序
                nearby_places.sort(key=lambda x: x['distance'])

                print(f'找到 {len(nearby_places)} 個距離 {building[3]} 5公里內的景點')
            except Exception as e:
                print('計算景點距離時發生錯誤:', e)
                traceback.print_exc()
                # 如果從資料庫計算失敗，使用 API 獲取
                lat, lng = building[13], building[14]
                places_api = get_nearby_places(lat, lng, max_distance_km=5)
                for n, a, t, d in places_api:
                    nearby_places.append(
                        {
                            'name': n,
                            'eng_name': '',
                            'dis': '',  # 新增
                            'eng_dis': '',  # 新增
                            'address': a,
                            'eng_address': '',
                            'type': t,
                            'eng_type': '',
                            'info': '',
                            'eng_info': '',
                            'lat': 0,  # 新增預設值
                            'lng': 0,  # 新增預設值
                            'distance': float(d) if isinstance(d, (int, float)) else 0,
                            'is_building': False,  # 標記為景點
                        }
                    )
                print('改用 API 取得附近景點，找到', len(nearby_places), '個景點')
            try:
                # 獲取所有建築物資料（除了當前建築物）
                cur.execute("SELECT * FROM buildings WHERE id != ?", (building[0],))
                all_buildings = cur.fetchall()

                if all_buildings:
                    # 計算每個建築物與當前建築物的距離
                    for b in all_buildings:
                        # buildings 表結構: id, label_name, eng_name, name, dis, eng_dis, address, eng_address, type, eng_type, desc, en_desc, img, lat, lng
                        b_lat = b[13]  # lat 索引
                        b_lng = b[14]  # lng 索引

                        # 計算距離
                        distance = calculate_distance(building_lat, building_lng, b_lat, b_lng)

                        # 僅選擇距離在 5 公里內的建築物
                        if distance <= 5:
                            nearby_places.append(
                                {
                                    'name': b[3],  # name
                                    'eng_name': b[2],  # eng_name
                                    'dis': b[4],  # dis - 新增
                                    'eng_dis': b[5],  # eng_dis - 新增
                                    'address': b[6],  # address
                                    'eng_address': b[7],  # eng_address
                                    'type': b[8] or '地標',  # type
                                    'eng_type': b[9] or 'Landmark',  # eng_type
                                    'desc': b[10],  # desc - 修正
                                    'en_desc': b[11],  # en_desc - 修正
                                    'lat': b[13],  # lat
                                    'lng': b[14],  # lng
                                    'distance': round(distance, 2),
                                    'is_building': True,
                                }
                            )

                    # 重新根據距離排序
                    nearby_places.sort(key=lambda x: x['distance'])

            except Exception as e:
                print('計算建築物距離時發生錯誤:', e)
                traceback.print_exc()

            con.close()

        except Exception as e:
            traceback.print_exc()
            return jsonify({'error': f'資料庫查詢錯誤: {str(e)}'})

        # 使用 jsonify 確保回傳的 JSON 格式正確
        response_data = {
            'label_name': label_name,
            'building': {
                'id': building[0],
                'label_name': building[1],
                'eng_name': building[2],
                'name': building[3],
                'dis': building[4],
                'eng_dis': building[5],
                'address': building[6],
                'eng_address': building[7],
                'type': building[8],
                'eng_type': building[9],
                'desc': building[10],  # data 欄位對應 desc
                'en_desc': building[11],  # eng_data 欄位對應 en_desc
                'img': building[12],  # path 欄位對應 img
                'lat': building[13],
                'lng': building[14],
            },
            'nearby_places': nearby_places,
        }
        # 清理資料中的開頭空格
        cleaned_response = clean_data(response_data)
        return jsonify(cleaned_response)

    except Exception as e:
        traceback.print_exc()
        print('後端錯誤:', e)
        return jsonify({'error': f'後端錯誤: {str(e)}'})


@app.route('/places_by_area', methods=['GET'])
def get_places_by_area():
    try:
        # 從請求中獲取區域參數
        area = request.args.get('area')
        if not area:
            return jsonify({'error': '未指定區域'})

        print(f'搜尋區域: {area}')

        # 資料庫查詢
        try:
            con = sqlite3.connect('buildings.db')
            cur = con.cursor()

            # 先查詢此區域的建築物
            query_buildings = "SELECT * FROM buildings WHERE address LIKE ? OR name LIKE ?"
            search_pattern = f"%{area}%"
            cur.execute(query_buildings, (search_pattern, search_pattern))
            buildings_in_area = cur.fetchall()

            # 再查詢此區域的景點
            query_places = "SELECT * FROM places WHERE address LIKE ? OR name LIKE ?"
            cur.execute(query_places, (search_pattern, search_pattern))
            places_in_area = cur.fetchall()

            # 整理回傳資料
            result_buildings = []
            for b in buildings_in_area:
                result_buildings.append(
                    {
                        'id': b[0],
                        'label_name': b[1],
                        'eng_name': b[2],
                        'name': b[3],
                        'dis': b[4],
                        'eng_dis': b[5],
                        'address': b[6],
                        'eng_address': b[7],
                        'type': b[8],
                        'eng_type': b[9],
                        'desc': b[10],  # data 欄位對應 desc
                        'en_desc': b[11],  # eng_data 欄位對應 en_desc
                        'img': b[12],  # path 欄位對應 img
                        'lat': b[13],
                        'lng': b[14],
                        'is_building': True,
                    }
                )

            result_places = []
            for p in places_in_area:
                # places 表結構: id, name, eng_name, address, eng_address, type, eng_type, info, eng_info, lat, lng
                result_places.append(
                    {
                        'id': p[0],
                        'name': p[1],
                        'eng_name': p[2],
                        'dis': p[3],  # 新增
                        'eng_dis': p[4],  # 新增
                        'address': p[5],  # 修改索引
                        'eng_address': p[6],  # 修改索引
                        'type': p[7],  # 修改索引
                        'eng_type': p[8],  # 修改索引
                        'info': p[9],  # 修改索引
                        'eng_info': p[10],  # 修改索引
                        'lat': p[11],  # 修改索引
                        'lng': p[12],  # 修改索引
                        'is_building': False,
                    }
                )

            result_buildings = clean_data(result_buildings)  # 清理資料中的開頭空格
            result_places = clean_data(result_places)  # 清理資料中的開頭空格
            # 合併結果
            all_places = result_buildings + result_places

            print(
                f'在 {area} 區域找到 {len(all_places)} 個地點 (建築物: {len(result_buildings)}, 景點: {len(result_places)})'
            )

            con.close()
            return jsonify({'area': area, 'places': all_places})

        except Exception as e:
            traceback.print_exc()
            return jsonify({'error': f'資料庫查詢錯誤: {str(e)}'})

    except Exception as e:
        traceback.print_exc()
        print('後端錯誤:', e)
        return jsonify({'error': f'後端錯誤: {str(e)}'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
