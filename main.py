import ctypes
import json
import os
import platform
import re
import readline
import shutil
import socket
import subprocess
import sys
import tarfile
import threading
import time

import requests
from tqdm import tqdm

os_type = platform.system()
architecture = platform.architecture()[0]
machine_type = platform.machine()


def update_json() -> None:
    json_url = "https://java.r18.icu/json_version"
    try:
        data = requests.get(json_url).json()
        if data["version"] != config["version"]:
            print("发现新版本，正在更新...")
            with open("config.json", "w") as f:
                json.dump(data, f)
            print("更新完成")
        else:
            print("已经是最新版本")
    except:
        print("更新失败")


def download_file(url, filename):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    with open(filename, "wb") as file, tqdm(
        desc=filename,
        total=total_size,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)
                bar.update(len(chunk))


def update_config_with_stable_versions(config_file_path):
    # URLs for the JSON data
    game_url = "https://meta.fabricmc.net/v2/versions/game"
    loader_url = "https://meta.fabricmc.net/v2/versions/loader"
    installer_url = "https://meta.fabricmc.net/v2/versions/installer"

    # 获取 JSON 数据
    game_response = requests.get(game_url)
    loader_response = requests.get(loader_url)
    installer_response = requests.get(installer_url)

    game_data = game_response.json()
    loader_data = loader_response.json()
    installer_data = installer_response.json()

    # 过滤稳定版本
    stable_game_versions = [
        version["version"] for version in game_data if version["stable"]
    ]
    stable_loader_versions = [
        version["version"] for version in loader_data if version["stable"]
    ]
    stable_installer_versions = [
        version["version"] for version in installer_data if version["stable"]
    ]

    # 创建所有组合
    combinations = [
        (game, loader, installer)
        for game in stable_game_versions
        for loader in stable_loader_versions
        for installer in stable_installer_versions
    ]

    # 基础 URL
    base_url = "https://meta.fabricmc.net/v2/versions/loader"

    # 创建字典以存储游戏版本和对应的 URL
    version_url_dict = {}

    # 请求每个组合的 URL 并将状态码为 200 的 URL 添加到字典中
    for game_version, loader_version, installer_version in combinations:
        url = (
            f"{base_url}/{game_version}/{loader_version}/{installer_version}/server/jar"
        )
        version_url_dict[game_version] = url

    # 读取现有的 config.json 文件
    with open(config_file_path, "r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)

    # 将新版本链接追加到现有字典中
    if "fabric" not in config_data:
        config_data["fabric"] = {}

    config_data["fabric"].update(version_url_dict)

    # 将更新后的字典写回到 config.json 文件
    with open(config_file_path, "w", encoding="utf-8") as config_file:
        json.dump(config_data, config_file, indent=4, ensure_ascii=False)

    print(f"总共找到 {len(combinations)} 种组合")
    print(f"更新了 {len(version_url_dict)} 个稳定版链接")

    return config_data


def download_jar():
    global choice, kind
    while True:
        try:
            kind = int(
                input("\n您想获取的游戏客户端\n1：Paper\n2：Fabric\n\n请输入序号： ")
            )
            if kind in [1, 2]:
                break
            else:
                print("无效的输入，请输入 1 或 2。")
        except ValueError:
            print("无效的输入，请输入一个数字 1 或 2。")

    if kind == 1:
        print("\n你选择了 Paper")
        print("\n共找到以下版本(每行输出5个)\n")
        count = 0
        for version in config["paper"].keys():
            print(version, end=" ")
            count += 1
            if count % 5 == 0:
                print()
        if count % 5 != 0:
            print()

        while True:
            choice = str(input("\n请输入要下载的版本号: "))
            if choice in config["paper"].keys():
                print(f"你选择了版本 {choice} 正在开始下载\n")
                break
            else:
                print("无效的版本号，请重新输入")

        download_url = config["paper"][choice]
        download_file(download_url, f"{choice}.jar")

    elif kind == 2:
        print("\n你选择了 Fabric")
        print("\n共找到以下版本(每行输出5个)\n")
        count = 0
        for version in config["fabric"].keys():
            print(version, end=" ")
            count += 1
            if count % 5 == 0:
                print()
        if count % 5 != 0:
            print()

        while True:
            choice = str(input("\n请输入要下载的版本号: "))
            if choice in config["fabric"].keys():
                print(f"你选择了版本 {choice} 正在开始下载\n")
                break
            else:
                print("无效的版本号，请重新输入")

        download_url = config["fabric"][choice]
        download_file(download_url, f"{choice}.jar")


def get_java_version_for_choice():
    for java_version_int, versions in config["java"].items():
        if choice in versions:
            return java_version_int
    return None


def judgment_architecture():

    print(f"操作系统类型: {os_type}")
    print(f"系统架构: {architecture}")
    print(f"机器类型: {machine_type}")
    if (os_type == "Windows" and architecture != "64bit") or (
        os_type == "Windows" and machine_type != "AMD64"
    ):
        print("抱歉，该脚本暂时只支持64位的AMD64 Windows系统")
        exit()

    elif os_type == "Linux" and architecture != "64bit":
        print("抱歉，该脚本暂时只支持64位Linux系统")
        exit()


def extract_version_from_string(java_string):
    match = re.search(r"\d+", java_string)
    if match:
        return match.group(0)
    return None


def check_java(java_version_int):
    try:
        # 执行 "java -version"，获取版本信息
        result = subprocess.run(
            ["java", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            print("Java is not installed.")
            return False
    except FileNotFoundError:
        print("Java is not installed or not in PATH.")
        return False

    version_output = result.stderr
    match = re.search(r"\"(\d+\.\d+|\d+)\.\d+.*\"", version_output)

    if match:
        java_version_str = match.group(1)
        # 处理 Java 9 及以上版本（简化版号，如 17 而非 1.17）
        java_version_int = int(java_version_str.split(".")[0])
    else:
        print("Failed to detect Java version.")
        return False

    print(f"Detected Java version: {java_version_int}")

    if java_version_int != java_version_int:
        print(
            f"Java version mismatch. Expected: {java_version_int}, Found: {java_version_int}"
        )
        return False

    # 获取 Java 安装路径
    try:
        if sys.platform.startswith("win"):
            result = subprocess.run(
                ["where", "java"], stdout=subprocess.PIPE, text=True
            )
        else:
            result = subprocess.run(
                ["which", "java"], stdout=subprocess.PIPE, text=True
            )

        java_path = result.stdout.strip()
        if java_path:
            print(f"Java Path: {java_path}")
            return java_path
        else:
            print("Java is not found in PATH.")
            return False
    except Exception as e:
        print(f"Error while fetching Java path: {e}")
        return False


def get_java():
    global java_path
    java_version_int = extract_version_from_string(get_java_version_for_choice())
    java_path = check_java(int(java_version_int))
    if java_path:
        print("Java 已安装")
    else:
        if os_type == "Windows":
            java_path = rf"C:\Program Files\Java\jdk-{java_version_int}\bin\java.exe"
            if java_version_int == "8":
                java_path = r"C:\Program Files\Java\jre1.8.0_421\bin\java.exe"
        elif os_type == "Linux":

            base_dir = rf"/opt/java{java_version_int}"
            subfolder_path = next(
                (
                    os.path.join(base_dir, d)
                    for d in os.listdir(base_dir)
                    if os.path.isdir(os.path.join(base_dir, d))
                ),
                None,
            )
            java_path = os.path.join(subfolder_path, "bin", "java")

        if os.path.exists(java_path):
            return None

        print(f"\n所需的Java版本为：{java_version_int}\n")
        java_url_data = config["java_url"][os_type]
        if os_type == "Windows":
            java_url = java_url_data["64bit"][java_version_int]
            suffix = "exe"
        elif os_type == "Linux":
            java_url = java_url_data[machine_type][java_version_int]
            suffix = "tar.gz"
        else:
            OSError("不支持的操作系统")
        file_name = f"{java_version_int}.{suffix}"
        print(java_url)

        download_file(java_url, file_name)
        print("\n安装Java中...\n")
        if os_type == "Windows":
            print(f"请手动完成Java{java_version_int}的安装,请不要更改Java的默认配置\n")
            subprocess.run(file_name, check=True)

        elif os_type == "Linux":
            with tarfile.open(file_name, "r:gz") as tar:
                tar.extractall(path=f"/opt/java{java_version_int}")
            if os.path.exists(java_path):
                pass
            else:
                RuntimeError("Java安装失败")
            # os.system(f"tar -xzf {file_name} -C /usr/lib/jvm")

        time.sleep(5)

        try:
            result = subprocess.run(
                [java_path, "--version"], capture_output=True, text=True, check=True
            )
            print("Java 版本输出:\n", result.stdout)
            if java_version_int in result.stdout:
                print(f"Java {java_version_int} 安装成功。")
            else:
                print(f"安装失败，安装的 Java 版本不匹配。")
        except subprocess.CalledProcessError as e:
            print(f"Java 安装失败，返回码: {e.returncode}")
            print(f"错误输出:\n{e.stderr}")
        except FileNotFoundError:
            print("Java 执行文件未找到，请检查 Java 是否正确安装。")

        print("\n开始清理下载缓存文件\n")
        os.remove(file_name)


def compare_versions(version1, version2):
    """
    比较两个版本号字符串，返回True如果version1大于或等于version2，否则返回False。
    """
    v1 = tuple(map(int, version1.split(".")))
    v2 = tuple(map(int, version2.split(".")))
    return v1 >= v2


def is_port_in_use(
    port: int,
    host="127.0.0.1",
):
    """检查指定主机和端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        return result == 0


def read_output(process):
    for line in iter(process.stdout.readline, b""):
        sys.stdout.write(line.decode())
        sys.stdout.flush()

    for line in iter(process.stderr.readline, b""):
        sys.stderr.write(line.decode())
        sys.stderr.flush()


def install_geyser():
    while True:
        choice_ = str(input("\n是否需要安装Geyser(间歇泉插件)与基岩版玩家同乐？ Y/N "))
        if choice_.upper() == "Y":
            if compare_versions(choice, "1.12.2"):
                pass
            else:
                print("Geyser只支持1.12.2及以上版本")
                exit()
            print(f"开始下载Geyser\n")
            break
        elif choice_.upper() == "N":
            exit()
        else:
            print("无效的选项，若不需要请输入：N")
    if kind == 1:
        download_url = config["geyser"]["paper"]
        geyser_name = "Geyser-Spigot.jar"
    elif kind == 2:
        download_url = config["geyser"]["fabric"]
        geyser_name = "Geyser-Fabric.jar"
    download_file(download_url, geyser_name)

    print("\nGeyser下载完成\n")
    print(os.getcwd())
    if kind == 1:
        shutil.move(geyser_name, os.path.join(os.getcwd(), "plugins", geyser_name))
        # mc_process = subprocess.run(
        #     command,
        #     capture_output=True,
        #     text=True,
        #     check=True,
        # )
        # sys.stdout.write(mc_process.stdout)
    elif kind == 2:
        print("fabric还是别装了，还得装fabric api")
        print("Bey~")
        sys.exit()
        # shutil.move(geyser_name, os.path.join(os.getcwd(), "mods", geyser_name))

    print("Loading...")
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )
    thread = threading.Thread(
        target=detection_start,
    )
    thread.start()
    thread.join()
    print("\nGeyser已启动\n")
    print()
    sys.exit()


def detection_start():
    stauts = 0
    while True:
        if is_port_in_use(25565):
            if stauts != 1:
                print("\n我的世界Java版正常启动！")
                stauts += 1

        if is_port_in_use(19132):
            if stauts != 2:
                print("\nGeyser正常启动！")
                stauts += 1

        if stauts == 2:
            print("\n自此，所有环节均已结束\nEnjoy the time!")
            break
        time.sleep(1)


def start_server():
    global command
    directory = f"minecraft_{choice}_server"
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.mkdir(directory)

    shutil.move(f"{choice}.jar", os.path.join(directory, f"{choice}.jar"))
    os.chdir(directory)
    print("\n开始测试启动")
    try:
        command = [java_path, "-jar", f"{choice}.jar", "nogui"]
        print(command)
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"启动出错：{e.stderr}")
    print("\nPaper 我的世界服务端已部署完成")
    print("\n正在修改eula.txt ...\n")
    with open("eula.txt", "w", encoding="utf-8") as f:
        f.write("eula=true")
    print("\n修改完成\n我的世界服务器部署完毕")
    print(f"\n启动命令为: {command}")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except AttributeError:
        return False


if __name__ == "__main__":
    if os_type == "Windows" and not is_admin():
        print("请以管理员运行")
        exit()
    readline.parse_and_bind('"\C-H": backward-delete-char')
    judgment_architecture()
    # 开发环境与实际应用
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)

    config_path = os.path.join(base_path, "config.json")
    config = json.loads(open(config_path, "r", encoding="utf-8").read())
    update_json()
    config = json.loads(
        open(config_path, "r", encoding="utf-8").read()
    )  # Load new config
    if "fabric" not in config:
        print("\n获取fabric下载链接中")
        config = update_config_with_stable_versions(config_path)
        print("\n获取fabric下载链接成功,更新配置文件")

    download_jar()
    get_java()
    start_server()
    install_geyser()
