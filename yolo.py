import cv2
from ultralytics import YOLO

model = YOLO('yolov8n.pt')


image_path = '1.jpg'
image = cv2.imread(image_path)

#  辨識圖片中的物件
results = model(image)

# 顯示辨識結果
annotated_frame = results[0].plot()

#  儲存辨識後的圖片
output_path = 'output.jpg'
cv2.imwrite(output_path, annotated_frame)

# 顯示結果圖片
cv2.imshow('YOLOv8 Detection', annotated_frame)
cv2.waitKey(0)
cv2.destroyAllWindows()
