import tempfile
import cv2
from ultralytics import YOLO


model_paths = {
    "s": "/pcb_v3_best.pt",   # YOLOv8s
    "n": "/pcb_v8n_best.pt",
    "m": "/pcb_v8m_best.pt"
}

def detect_image(image, model_size,path):
    model = YOLO(model_paths[model_size])
    results = model(image)
    annotated_img = results[0].plot()

    # Save annotated image as PNG in a temp file
    #temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    cv2.imwrite(path, annotated_img)

    return path

def get_detect(image,path):
    detect_image(image,"s",path)