import sqlite3

# if len(columns) == 14:
#     cur.execute(
#         "INSERT INTO buildings (label_name, eng_name, name, dis, eng_dis, address, eng_address, type, eng_type, data, eng_data, path, lat, lng) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
#         tuple(columns),
#     )
type = ""


def add_data_pla(txt_file: str):
    # 連接到 SQLite 資料庫 'buildings.db'
    con = sqlite3.connect('buildings.db')
    cur = con.cursor()  # 創建一個游標物件，讓我們能夠執行 SQL 查詢

    try:
        with open(txt_file, 'r', encoding='utf-8') as file:
            success_rows = 0
            for idx, line in enumerate(file, start=1):
                line = line.strip()
                if not line:  # 跳過空行
                    continue

                columns = line.split(',')
                if len(columns) == 12:
                    cur.execute(
                        "INSERT INTO places (name, eng_name, dis, eng_dis, address, eng_address, type, eng_type, info, eng_info, lat, lng) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        tuple(columns),
                    )
                    success_rows += 1
                else:
                    # 如果該行的格式不正確，顯示錯誤訊息
                    print(f"數據格式錯誤: {line} (欄位數: {len(columns)}, 預期: 12)")

        # 提交資料庫變更，保存新增的資料
        con.commit()
        # 打印提示，表示資料已經成功新增至資料庫
        print(f"資料已新增至資料庫 (共 {success_rows} 筆記錄)")
        return True  # 明確返回成功標誌
    except Exception as e:
        print(f"添加資料時發生錯誤: {e}")
        return False  # 明確返回失敗標誌
    finally:
        # 關閉資料庫連接
        con.close()


def add_data_bud(txt_file: str):
    # 連接到 SQLite 資料庫 'buildings.db'
    con = sqlite3.connect('buildings.db')
    cur = con.cursor()  # 創建一個游標物件，讓我們能夠執行 SQL 查詢

    try:
        with open(txt_file, 'r', encoding='utf-8') as file:
            success_rows = 0
            for idx, line in enumerate(file, start=1):
                line = line.strip()
                if not line:  # 跳過空行
                    continue

                columns = line.split(',')
                if len(columns) == 14:
                    cur.execute(
                        "INSERT INTO buildings (label_name, eng_name, name, dis, eng_dis, address, eng_address, type, eng_type, data, eng_data, path, lat, lng) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        tuple(columns),
                    )
                    success_rows += 1
                else:
                    # 如果該行的格式不正確，顯示錯誤訊息
                    print(f"數據格式錯誤: {line} (欄位數: {len(columns)}, 預期: 12)")

        # 提交資料庫變更，保存新增的資料
        con.commit()
        # 打印提示，表示資料已經成功新增至資料庫
        print(f"資料已新增至資料庫 (共 {success_rows} 筆記錄)")
        return True  # 明確返回成功標誌
    except Exception as e:
        print(f"添加資料時發生錯誤: {e}")
        return False  # 明確返回失敗標誌
    finally:
        # 關閉資料庫連接
        con.close()


def fetch_data_by_label(label: str):
    try:

        con = sqlite3.connect('buildings.db')
        cur = con.cursor()

        cur.execute("SELECT * FROM buildings WHERE label_name = ?", (label,))

        matched_data = cur.fetchall()
        con.close()

        return matched_data

    except sqlite3.Error as e:
        print(f"數據庫錯誤: {e}")
        return []


def clear_all_places():
    """
    清空 places 表的所有資料，但保留表格結構
    """
    try:
        con = sqlite3.connect('buildings.db')
        cur = con.cursor()

        # 刪除所有資料
        cur.execute("DELETE FROM places")

        deleted_count = cur.rowcount
        con.commit()

        print(f"已清空 places 表，刪除了 {deleted_count} 筆資料")

        # 重置自動遞增的 ID（可選）
        cur.execute("DELETE FROM sqlite_sequence WHERE name='places'")
        con.commit()
        print("已重置 ID 序列")

        con.close()
        return True

    except sqlite3.Error as e:
        print(f"清空資料時發生錯誤: {e}")
        return False


def delete_places_by_ids(ids_list, data_name: str):
    """
    刪除指定 ID 的 places 資料

    Args:
        ids_list: 要刪除的 ID 列表，例如 [11, 13, 17, 18, 19, 20]
    """
    try:
        con = sqlite3.connect('buildings.db')
        cur = con.cursor()

        # 先檢查這些 ID 是否存在
        placeholders = ','.join('?' * len(ids_list))
        check_query = f"SELECT id, name FROM {data_name} WHERE id IN ({placeholders})"
        cur.execute(check_query, ids_list)
        existing_records = cur.fetchall()

        if existing_records:
            print("將要刪除的資料：")
            for record in existing_records:
                print(f"  ID: {record[0]}, 名稱: {record[1]}")

        # 執行刪除
        delete_query = f"DELETE FROM {data_name} WHERE id IN ({placeholders})"
        cur.execute(delete_query, ids_list)

        deleted_count = cur.rowcount
        con.commit()

        print(f"成功刪除 {deleted_count} 筆資料")

        con.close()
        return True

    except sqlite3.Error as e:
        print(f"刪除資料時發生錯誤: {e}")
        return False
