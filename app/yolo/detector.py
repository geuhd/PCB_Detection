from ultralytics import YOLO
import cv2
import os
import pathlib
import traceback
import sys
import platform

try:
    import torch
except Exception:
    torch = None

# --- Configuration ---
BASE_DIR = pathlib.Path(__file__).resolve().parent  # absolute
MODEL_PATHS = {
    "v3":  BASE_DIR / "pcb_v3_best .pt",
    "v8m": BASE_DIR / "pcb_v8m_best.pt",
    "v8n": BASE_DIR / "pcb_v8n_best.pt",
}

YOLO_MODELS_CACHE = {}


def _log_env():
    print("=== ENV DEBUG ===")
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.platform()}")
    try:
        import ultralytics
        print(f"Ultralytics: {ultralytics.__version__}")
    except Exception:
        print("Ultralytics: <unknown>")

    if torch:
        print(f"PyTorch: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA device count: {torch.cuda.device_count()}")
            print(f"CUDA current device: {torch.cuda.current_device()}")
    print("=================")


def load_yolo_model(model_name: str) -> YOLO:
    global YOLO_MODELS_CACHE

    print(f"[load_yolo_model] requested: '{model_name}'")
    if model_name in YOLO_MODELS_CACHE:
        print(f"[load_yolo_model] returning cached model '{model_name}'")
        return YOLO_MODELS_CACHE[model_name]

    if model_name not in MODEL_PATHS:
        msg = f"Unknown model name '{model_name}'. Expected one of {list(MODEL_PATHS.keys())}"
        print("[load_yolo_model] CRITICAL:", msg)
        raise ValueError(msg)

    model_path = MODEL_PATHS[model_name]
    print(f"[load_yolo_model] resolved model_path: {model_path} (exists={model_path.exists()})")
    if model_path.exists():
        try:
            size = model_path.stat().st_size
        except Exception:
            size = -1
        print(f"[load_yolo_model] model file size: {size} bytes")

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    try:
        _log_env()
        print(f"[load_yolo_model] Loading YOLO model from: {model_path}")
        model = YOLO(str(model_path))  # str() for safety
        YOLO_MODELS_CACHE[model_name] = model
        print(f"[load_yolo_model] Model '{model_name}' loaded & cached.")
        return model
    except Exception as e:
        print(f"[load_yolo_model] CRITICAL: failed to load model '{model_name}' from '{model_path}'")
        traceback.print_exc()
        raise e


def run_yolo_detection(
    model_name: str,
    original_image_path: str,
    output_image_path: str
) -> bool:
    print("=== run_yolo_detection START ===")
    print(f"model_name={model_name}")
    print(f"original_image_path={os.path.abspath(original_image_path)} (exists={os.path.exists(original_image_path)})")
    print(f"output_image_path={os.path.abspath(output_image_path)}")

    # Extra image sanity check BEFORE YOLO
    try:
        # Try reading with OpenCV to ensure file is valid image
        img = cv2.imread(original_image_path)
        if img is None:
            print("[run_yolo_detection] OpenCV could not read the input image (None).")
        else:
            h, w = img.shape[:2]
            print(f"[run_yolo_detection] OpenCV read success: shape={w}x{h}")
    except Exception as e:
        print("[run_yolo_detection] OpenCV read raised exception:")
        traceback.print_exc()

    try:
        model = load_yolo_model(model_name)
        if model is None:
            print("[run_yolo_detection] ERROR: load_yolo_model returned None")
            return False

        print("[run_yolo_detection] Running model.predict(...)")
        results = model.predict(
            source=original_image_path,
            conf=0.25,
            iou=0.7,
            save=False,
            device='cpu'
        )

        # Basic results sanity
        if not results or len(results) == 0:
            print("[run_yolo_detection] ERROR: YOLO returned empty results list.")
            return False

        r0 = results[0]
        try:
            names = getattr(r0, "names", None)
            boxes = getattr(r0, "boxes", None)
            n_boxes = int(len(boxes)) if boxes is not None and hasattr(boxes, "__len__") else "unknown"
            print(f"[run_yolo_detection] result[0]: names_present={names is not None}, boxes_count={n_boxes}")
        except Exception:
            print("[run_yolo_detection] Could not inspect results[0]; continuing...")

        print("[run_yolo_detection] Plotting annotated image")
        annotated_img = r0.plot()
        if annotated_img is None:
            print("[run_yolo_detection] ERROR: plot() returned None")
            return False

        print("[run_yolo_detection] Writing annotated image with cv2.imwrite")
        ok = cv2.imwrite(output_image_path, annotated_img)
        print(f"[run_yolo_detection] cv2.imwrite returned: {ok}")
        if not ok:
            print("[run_yolo_detection] ERROR: Failed to write the annotated image.")
            return False

        print(f"[run_yolo_detection] SUCCESS. Saved to: {output_image_path}")
        print("=== run_yolo_detection END (SUCCESS) ===")
        return True

    except Exception as e:
        print("[run_yolo_detection] EXCEPTION during detection/save:")
        print(f"Type: {type(e).__name__}  Message: {e}")
        traceback.print_exc()
        print("=== run_yolo_detection END (FAIL) ===")
        return False
