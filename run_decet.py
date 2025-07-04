import logging
import os

from ultralytics import YOLO
from ultralytics.utils import DEFAULT_CFG

from Database_Helper import fetch_data_by_label as fd

# 设置日志级别
logging.getLogger('ultralytics').setLevel(logging.ERROR)

model = YOLO('decet.pt')


def detect_labels(image_folder: str):
    """
    使用 YOLO 模型檢測圖像中的標籤。

    参数：
        image_folder (str): 包含圖像的文件路徑。
        model_path (str): 訓練好的模型文件路徑。
        conf_threshold (float): 置信度閥值，默认是 0.70。

    返回：
        dict: 包含圖片文件路徑和其對應檢測到的標籤的資料。
    """
    try:
        # 加載預訓練模型

        # 執行預測
        results = model.predict(
            source=image_folder, save=False, conf=0.5, imgsz=512, half=False, device="cpu"
        )

        # 處理每個預測結果
        for r in results:
            if r.boxes is not None and len(r.boxes.cls) > 0:
                label_idx = int(r.boxes.cls[0].cpu().numpy())
                return model.names[label_idx]

        return "無辨識結果"

    except Exception as e:
        return f"錯誤：{str(e)}"
