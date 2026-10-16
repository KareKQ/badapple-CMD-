
import os
import sys
import time
import cv2

# ============ 可调参数 ============
VIDEO_PATH = "badapple.mp4"   # 视频文件路径（同目录或绝对路径）
WIDTH      = 120           # 字符宽度（列数），推荐 80~120
HEIGHT     = 50               # 字符高度（行数），推荐 24~35
ASPECT     = 2.0              # 字符宽高比修正，字符通常是 1:2，所以填 2.0
GAMMA      = 1              # 伽马校正，<1 提亮暗部，>1 压暗
TARGET_FPS = 80            # 目标帧率
COLOR      = True             # 是否彩色输出（需 Windows Terminal，性能会下降）
LOOP       = False            # 是否循环播放

# 从暗到亮的字符集
CHARS = "10"


# ============ ANSI 控制码 ============
ESC        = "\033["
CLEAR      = ESC + "2J"
HOME       = ESC + "H"
HIDE_CURSOR = ESC + "?25l"
SHOW_CURSOR = ESC + "?25h"
RESET      = ESC + "0m"


def frame_to_ascii(frame, width, height):
    """把一帧彩色图像转换成 ASCII 字符串"""
    h, w = frame.shape[:2]
    aspect = w / h

    # 按终端字符尺寸计算缩放后的分辨率
    new_w = width
    new_h = int(new_w / aspect / ASPECT)
    if new_h > height:
        new_h = height
        new_w = int(new_h * aspect * ASPECT)
    new_w = max(new_w, 1)
    new_h = max(new_h, 1)

    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    if COLOR:
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        lines = []
        for y in range(new_h):
            row_chars = []
            for x in range(new_w):
                p = gray[y, x]
                idx = int((p / 255.0) ** GAMMA * (len(CHARS) - 1))
                ch = CHARS[idx]
                r, g, b = rgb[y, x]
                row_chars.append(f"{ESC}38;2;{r};{g};{b}m{ch}")
            row_chars.append(RESET)
            lines.append("".join(row_chars))
        return "\n".join(lines)
    else:
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        lines = []
        for row in gray:
            line = "".join(
                CHARS[int((p / 255.0) ** GAMMA * (len(CHARS) - 1))]
                for p in row
            )
            lines.append(line)
        return "\n".join(lines)


def main():
    if not os.path.exists(VIDEO_PATH):
        print(f"找不到视频文件：{VIDEO_PATH}")
        print("请把 badapple.mp4 放到脚本同目录，或修改 VIDEO_PATH。")
        return

    # 让 Windows 终端启用 ANSI 转义
    if os.name == "nt":
        os.system("")

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("无法打开视频，请检查文件是否损坏或缺少解码器。")
        return

    src_fps = cap.get(cv2.CAP_PROP_FPS)
    if src_fps <= 0 or src_fps > 240:
        src_fps = 30.0
    print(f"视频原始帧率：{src_fps:.2f} FPS")

    # 设置窗口大小
    os.system(f"mode con cols={WIDTH} lines={HEIGHT + 2}")

    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.flush()

    frame_time = 1.0 / TARGET_FPS
    next_time = time.perf_counter()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if LOOP:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            ascii_frame = frame_to_ascii(frame, WIDTH, HEIGHT)

  
            sys.stdout.write(HOME + ascii_frame + RESET)
            sys.stdout.flush()

   
            next_time += frame_time
            sleep = next_time - time.perf_counter()
            if sleep > 0:
                time.sleep(sleep)
            else:

                next_time = time.perf_counter()

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR + RESET)
        sys.stdout.flush()
        cap.release()
        print("\n播放结束")


if __name__ == "__main__":
    main()