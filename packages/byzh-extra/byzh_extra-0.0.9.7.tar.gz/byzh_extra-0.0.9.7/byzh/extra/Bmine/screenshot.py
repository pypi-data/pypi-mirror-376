import requests
import m3u8
import subprocess
import os
from concurrent.futures import ThreadPoolExecutor

from byzh.core.Btqdm import B_Tqdm

def get_screenshot(url: str, output_path="screenshot.jpg", timeout: int = 10) -> bool:
    # 检测 m3u8 链接是否可播放
    flag = False
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200 or not response.text.strip():
            return False

        playlist = m3u8.loads(response.text)
        flag = bool(playlist.segments or playlist.playlists)
    except Exception:
        flag = False

    # ffmpeg 命令，取第 1 秒的一帧
    if flag:
        cmd = [
            "ffmpeg",
            "-y",  # 覆盖输出
            "-i", url,  # 输入 m3u8
            "-ss", "00:00:01",  # 定位到第 1 秒
            "-vframes", "1",  # 取 1 帧
            output_path
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            # print(f"截图成功：{output_path}")
            return True
        except subprocess.CalledProcessError:
            return False
    return False

def get_screenshot_for_Xidian(base:int, output_dir, pre_delta=100, post_delta=100):
    os.makedirs(output_dir, exist_ok=True)
    prefix = "http://202.117.115.59:8092/pag/202.117.115.50/7302/"
    suffix = "/0/MAIN/TCP/live.m3u8"

    url_lst = []
    output_path_lst = []
    for bias in range(-pre_delta, post_delta):
        url = f"{prefix}00{base+bias}{suffix}"
        output_path = os.path.join(output_dir, f"00{base+bias}.jpg")
        url_lst.append(url)
        output_path_lst.append(output_path)

    my_tqdm = B_Tqdm(len(url_lst))

    def get_screenshot2(url: str, output_path="screenshot.jpg"):
        get_screenshot(url, output_path)
        my_tqdm.update(1)

    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(pre_delta+post_delta):
            executor.submit(get_screenshot2, url_lst[i], output_path_lst[i])


if __name__ == "__main__":
    get_screenshot_for_Xidian(9136, 'sc')


