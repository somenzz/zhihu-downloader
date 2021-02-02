import os, sys
import re
import click
import requests
from datetime import datetime


def get(url: str) -> list:
    """
    获取知乎视频的 url
    返回格式
    [{'url':'', 'title','format':'',},{}]
    """
    data = []
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    }

    html_content = "" 
    with requests.get(url, headers=headers, timeout=10) as rep:
        if rep.status_code == 200:
            html_content = rep.text
        else:
            print(f"网络连接失败，状态码 { rep.status_code }")
            return []

    #接口1 
    ids = re.findall(r"www.zhihu.com/zvideo/(\d{1,})", rep.text)
    ids = list(set(ids))  # 去掉重复元素
    for id in ids:
        print(id)
        with requests.get(
            f"https://www.zhihu.com/api/v4/zvideos/{id}/card",
            headers=headers,
            timeout=10,
        ) as rep:
            if rep.status_code == 200:
                ret_data = rep.json()
                playlist = ret_data["video"]["playlist"]
                title = ret_data.get("title")
                temp = playlist.get("ld") or playlist.get("sd")
                if temp:
                    sigle_video = {}
                    sigle_video["url"] = temp.get("play_url")
                    sigle_video["title"] = title
                    sigle_video["format"] = temp.get("format")
                    data.append(sigle_video)
            else:
                print(f"网络连接失败，状态码 { rep.status_code }")



    #接口2 
    ids = re.findall(r'www.zhihu.com/video/(\d{1,})', rep.text)
    ids = list(set(ids)) # 去掉重复元素
    for id in ids:
        rep = requests.get(f"https://lens.zhihu.com/api/v4/videos/{id}", headers=headers, timeout=10)
        if rep.status_code == 200:
            ret_data = rep.json()
            playlist = ret_data["playlist"]
            title = ret_data.get("title")
            temp = playlist.get("HD") or playlist.get("SD") or playlist.get("LD")
            if temp:
                sigle_video = {}
                sigle_video["url"] = temp.get("play_url")
                sigle_video["title"] = title
                sigle_video["format"] = temp.get("format")
                data.append(sigle_video)
            else:
                print(f"网络连接失败，状态码 { rep.status_code }")

    if(len(data) == 0):
        print(f"该页面可能没有视频")

    #再次去重
    tmp_set = set()
    distince_data = []
    for x in data:
        if x['url'] in tmp_set:
            pass
        else:
            distince_data.append(x) 
            tmp_set.add(x['url'])
    
    print(f"该页面有 {len(distince_data)} 个视频")
    return distince_data  


def download(
    file_url,
    file_name=None,
    file_type=None,
    save_path="download",
    headers=None,
    timeout=15,
):
    """
    :param file_url: 下载资源链接
    :param file_name: 保存文件名，默认为当前日期时间
    :param file_type: 文件类型(扩展名)
    :param save_path: 保存路径，默认为download,后面不要"/"
    :param headers: http请求头
    """
    if file_name is None or file_name == "":
        file_name = str(datetime.now())

    if file_type is None:
        if "." in file_url:
            file_type = file_url.split(".")[-1]
        else:
            file_type = "uknown"

    file_name = file_name + "." + file_type

    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B137 Safari/601.1"
        }

    if os.path.exists(save_path):
        pass
    else:
        os.mkdir(save_path)

    # 下载提示

    if os.path.exists(f"{save_path}/{file_name}"):
        print(f"\033[33m{file_name}已存在，不再下载！\033[0m")
        return True

    print(f"Downloading {file_name}")
    try:
        with requests.get(
            file_url, headers=headers, stream=True, timeout=timeout
        ) as rep:
            file_size = int(rep.headers["Content-Length"])
            if rep.status_code != 200:
                print("\033[31m下载失败\033[0m")
                return False
            label = "{:.2f}MB".format(file_size / (1024 * 1024))
            with click.progressbar(length=file_size, label=label) as progressbar:
                with open(f"{save_path}/{file_name}", "wb") as f:
                    for chunk in rep.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            progressbar.update(1024)
            print(f"\033[32m{file_name}下载成功\033[0m")
    except Exception as e:
        print("下载失败: ", e)
    return True


if __name__ == "__main__":
    videos = get(sys.argv[1])
    for video in videos:
        download(
            file_url=video["url"],
            file_name=video["title"],
            file_type=video["format"],
            save_path="./tmp_download",
        )
