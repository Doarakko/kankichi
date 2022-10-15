import datetime
import glob
import os

import cv2
from dotenv import load_dotenv
from slack_sdk import WebClient

load_dotenv()

client = WebClient(os.environ.get("SLACK_BOT_TOKEN"))

IMAGE_DIR = "images"
IMAGE_LOG_DIR = "logs"


def generate_filename(prefix):
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{IMAGE_DIR}/{IMAGE_LOG_DIR}/{now}_{prefix}.png"


def take_picture():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()

    if ret:
        filename = generate_filename("log")
        cv2.imwrite(filename, frame)
        return filename

    raise Exception("failed to take picture")


def get_diff_count():
    images = glob.glob(f"{IMAGE_DIR}/{IMAGE_LOG_DIR}/*_log.png")
    images.sort()

    img_ref = cv2.imread(images[len(images) - 2], 1)
    img_comp = cv2.imread(images[len(images) - 1], 1)
    temp = img_comp.copy()

    gray_img_ref = cv2.cvtColor(img_ref, cv2.COLOR_BGR2GRAY)
    gray_img_comp = cv2.cvtColor(img_comp, cv2.COLOR_BGR2GRAY)
    gray_img_ref = cv2.blur(gray_img_ref, (3, 3))
    img_diff = cv2.absdiff(gray_img_ref, gray_img_comp)

    _, img_bin = cv2.threshold(img_diff, 50, 255, 0)
    contours, _ = cv2.findContours(img_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)

    count = 0
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if width > 50 or height > 50:
            cv2.rectangle(
                temp, (x - 2, y - 2), (x + width + 2, y + height + 2), (0, 255, 0), 1
            )
            count += 1
        else:
            continue

    filename = generate_filename("result")
    cv2.imwrite(filename, temp)

    return filename, count


def post_slack(filename, count):
    try:
        file = open(filename, "rb")
        new_file = client.files_upload(
            file=file,
        )
        file_url = new_file.get("file").get("permalink")

        client.chat_postMessage(
            channel=os.environ.get("SLACK_CHANNEL_NAME"),
            text=f"{count} diffs detected.\n{file_url}",
        )
    except Exception as e:
        print(e)


if __name__ == "__main__":
    try:
        filename = take_picture()
        filename, count = get_diff_count()
        print(f"{count} diffs detected")

        if count > 1:
            post_slack(filename, count)
    except Exception as e:
        print(e)
