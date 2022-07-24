import glob
import datetime

import cv2


IMAGE_DIR = "images"
IMAGE_LOG_DIR = "logs"

def generate_filename(prefix):
    return "{}/{}/{}_{}.png".format(
        IMAGE_DIR, IMAGE_LOG_DIR, datetime.datetime.now().strftime("%Y%m%d%H%M%S"), prefix)


def take_picture():
    cap = cv2.VideoCapture(0)

    ret, frame = cap.read()

    if ret:
        filename = generate_filename("log")
        cv2.imwrite(filename, frame)

        return filename
    else:
        raise Exception("failed to take picture")


def get_diff_count():
    images = glob.glob("{}/{}/*_log.png".format(IMAGE_DIR, IMAGE_LOG_DIR))
    images.sort()

    img_ref = cv2.imread(images[len(images)-2], 1)
    img_comp = cv2.imread(images[len(images)-1], 1)
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
            cv2.rectangle(temp, (x-2, y-2), (x+width+2, y+height+2), (0, 255, 0), 1)
            count += 1
        else:
            continue

    cv2.imwrite(generate_filename("result"), temp)

    return count


if __name__ == "__main__":
    try:
        take_picture()
        count = get_diff_count()
        print("{} diffs detected".format(count))
    except Exception as e:
        print(e)
