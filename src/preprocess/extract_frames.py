import cv2
import os

def extract_frames(video_path, output_folder, title, interval=30):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 100)

    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if count % interval == 0:
            cv2.imwrite(f"{output_folder}/{title}_frame_{count:06d}.jpg", frame)
        count += 1
    cap.release()

if __name__ == "__main__":
    data_folder = "../../data/videos"
    output_folder = "../../data/frames"
    os.makedirs(output_folder, exist_ok=True)
    

    for filename in os.listdir(data_folder):
        if filename.endswith(".mp4"):
            video_path = os.path.join(data_folder, filename)
            title = os.path.splitext(filename)[0]
            video_output_folder = os.path.join(output_folder, title)
            os.makedirs(video_output_folder, exist_ok=True)
            extract_frames(video_path, video_output_folder, title, interval=30)