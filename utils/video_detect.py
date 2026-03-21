import cv2
import numpy as np

def analyze_video(video_path):

    cap=cv2.VideoCapture(video_path)

    frames=0
    fake_score=0

    while True:

        ret,frame=cap.read()

        if not ret:
            break

        frames+=1

        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

        noise=np.var(gray)

        if noise>500:
            fake_score+=1

    cap.release()

    if frames==0:
        return "Unknown",50

    fake_percentage=(fake_score/frames)*100

    result="Fake" if fake_percentage>50 else "Real"

    return result,round(fake_percentage,2)