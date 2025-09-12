# 音频频道调整：将音频向前/向后平移若干秒
def shift_audio(input_path, output_path, shift_seconds):
    """
    input_path: 输入视频文件路径
    output_path: 输出视频文件路径
    shift_seconds: 音频平移秒数，正数为向后，负数为向前
    """
    try:
        # 提取音频，平移后再合成
        temp_audio = os.path.join(
            os.path.dirname(output_path), f"temp_audio_{get_timestamp()}.aac"
        )
        temp_video = os.path.join(
            os.path.dirname(output_path), f"temp_video_{get_timestamp()}.mp4"
        )
        # 1. 提取音频
        cmd_extract = ["ffmpeg", "-i", input_path, "-vn", "-acodec", "copy", temp_audio]
        subprocess.run(cmd_extract, check=True)
        # 2. 平移音频
        if shift_seconds >= 0:
            # 向后平移，前面补静音
            cmd_shift = [
                "ffmpeg",
                "-i",
                temp_audio,
                "-af",
                f"adelay={int(shift_seconds * 1000)}|{int(shift_seconds * 1000)}",
                temp_audio + "_shift.aac",
            ]
        else:
            # 向前平移，裁剪前面
            cmd_shift = [
                "ffmpeg",
                "-ss",
                str(-shift_seconds),
                "-i",
                temp_audio,
                "-acodec",
                "copy",
                temp_audio + "_shift.aac",
            ]
        subprocess.run(cmd_shift, check=True)
        # 3. 提取无音频视频
        cmd_video = ["ffmpeg", "-i", input_path, "-an", "-vcodec", "copy", temp_video]
        subprocess.run(cmd_video, check=True)
        # 4. 合成新视频
        cmd_merge = [
            "ffmpeg",
            "-i",
            temp_video,
            "-i",
            temp_audio + "_shift.aac",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            output_path,
        ]
        subprocess.run(cmd_merge, check=True)
        print(
            f"{Colors.GREEN}音频平移完成！输出文件已保存到 {output_path}{Colors.RESET}"
        )
        os.remove(temp_audio)
        os.remove(temp_audio + "_shift.aac")
        os.remove(temp_video)
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}音频平移失败：{e}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}发生错误：{e}{Colors.RESET}")


import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
from datetime import datetime


# 定义颜色常量
class Colors:
    GREEN = "\033[92m"  # 绿色
    YELLOW = "\033[93m"  # 黄色
    RED = "\033[91m"  # 红色
    RESET = "\033[0m"  # 重置颜色


# 获取当前时间戳
def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# 视频加速转换
def accelerate_video(input_path, output_path, speed_factor):
    try:
        command = [
            "ffmpeg",
            "-i",
            input_path,
            "-vf",
            f"setpts=PTS/{speed_factor}",
            "-af",
            (
                f"atempo={speed_factor}"
                if speed_factor <= 2.0
                else "atempo=2.0,atempo={}".format(speed_factor / 2.0)
            ),
            "-strict",
            "-2",
            output_path,
        ]
        subprocess.run(command, check=True)
        print(
            f"{Colors.GREEN}加速转换完成！输出文件已保存到 {output_path}{Colors.RESET}"
        )
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}加速转换失败：{e}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}发生错误：{e}{Colors.RESET}")


# 视频转换为 GIF 动图（提高分辨率）
def convert_to_gif(input_path, output_path, fps=10, scale=1080):
    try:
        command = [
            "ffmpeg",
            "-i",
            input_path,
            "-vf",
            f"fps={fps},scale={scale}:-1:flags=lanczos",  # 使用 lanczos 缩放算法提高质量
            "-c:v",
            "gif",
            output_path,
        ]
        subprocess.run(command, check=True)
        print(
            f"{Colors.GREEN}GIF 转换完成！输出文件已保存到 {output_path}{Colors.RESET}"
        )
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}GIF 转换失败：{e}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}发生错误：{e}{Colors.RESET}")


# 视频压缩
def compress_video(input_path, output_path, crf=28):
    try:
        command = [
            "ffmpeg",
            "-i",
            input_path,
            "-vcodec",
            "libx264",
            "-crf",
            str(crf),
            output_path,
        ]
        subprocess.run(command, check=True)
        print(
            f"{Colors.GREEN}视频压缩完成！输出文件已保存到 {output_path}{Colors.RESET}"
        )
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}视频压缩失败：{e}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}发生错误：{e}{Colors.RESET}")


def crop_video(input_path, output_path, start_time, end_time):
    """
    裁剪视频，保留从 start_time 到 end_time 的部分
    :param input_path: 输入视频文件路径
    :param output_path: 输出视频文件路径
    :param start_time: 开始时间（秒）
    :param end_time: 结束时间（秒）
    """
    try:
        duration = end_time - start_time  # 计算裁剪的时长
        command = [
            "ffmpeg",
            "-i",
            input_path,
            "-ss",
            str(start_time),  # 开始时间
            "-t",
            str(duration),  # 裁剪时长
            "-c",
            "copy",  # 直接复制流，不重新编码
            output_path,
        ]
        subprocess.run(command, check=True)
        print(
            f"{Colors.GREEN}视频裁剪完成！输出文件已保存到 {output_path}{Colors.RESET}"
        )
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}视频裁剪失败：{e}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}发生错误：{e}{Colors.RESET}")


# 批量裁剪：支持对单个视频裁剪出多个片段，支持批量输入
def batch_crop_videos(input_paths, segments, output_dir):
    """
    input_paths: list of video file paths
    segments: list of (start, end) tuples，单位秒
    output_dir: 输出目录
    """
    results = []
    for input_path in input_paths:
        base = os.path.splitext(os.path.basename(input_path))[0]
        for idx, (start, end) in enumerate(segments):
            output_path = os.path.join(
                output_dir,
                f"{base}_part{idx + 1}_start{start}_end{end}_{get_timestamp()}.mp4",
            )
            crop_video(input_path, output_path, start, end)
            results.append(output_path)
    return results


# 视频合并：将多个视频片段合并为一个视频
def merge_videos(input_paths, output_path):
    """
    input_paths: list of video file paths
    output_path: 合并后输出文件路径
    """
    try:
        # 生成临时文件列表
        list_file = os.path.join(
            os.path.dirname(output_path), f"merge_list_{get_timestamp()}.txt"
        )
        with open(list_file, "w") as f:
            for path in input_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")
        command = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_file,
            "-c",
            "copy",
            output_path,
        ]
        subprocess.run(command, check=True)
        print(
            f"{Colors.GREEN}视频合并完成！输出文件已保存到 {output_path}{Colors.RESET}"
        )
        os.remove(list_file)
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}视频合并失败：{e}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}发生错误：{e}{Colors.RESET}")


# 获取文件夹中的视频文件
def get_video_files(folder_path):
    video_extensions = [".mp4", ".mkv", ".avi", ".mov"]
    video_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if os.path.splitext(file)[1].lower() in video_extensions:
                video_files.append(os.path.join(root, file))
    return video_files


# GUI 界面
class VideoToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("视频处理工具")
        self.root.geometry("1500x550")  # 调整窗口尺寸，适配更多功能

        # 输入文件选择
        self.input_file_label = tk.Label(root, text="选择视频文件或文件夹：")
        self.input_file_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

        self.input_file_entry = tk.Entry(root, width=50)
        self.input_file_entry.grid(row=0, column=1, padx=10, pady=10)

        self.input_file_button = tk.Button(
            root, text="浏览", width=10, command=self.select_input
        )
        self.input_file_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        # 输出路径选择（调整到第 2 行）
        self.output_folder_label = tk.Label(root, text="选择输出文件夹（可选）：")
        self.output_folder_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

        self.output_folder_entry = tk.Entry(root, width=50)
        self.output_folder_entry.grid(row=1, column=1, padx=10, pady=10)

        self.output_folder_button = tk.Button(
            root, text="浏览", width=10, command=self.select_output_folder
        )
        self.output_folder_button.grid(row=1, column=2, padx=10, pady=10, sticky="w")

        # 加速转换（调整到第 3 行）
        self.speed_label = tk.Label(root, text="加速倍数：")
        self.speed_label.grid(row=2, column=0, padx=10, pady=10, sticky="e")

        self.speed_entry = tk.Entry(root, width=10)
        self.speed_entry.insert(0, "4.0")  # 默认加速倍数
        self.speed_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        self.accelerate_button = tk.Button(
            root, text="加速转换", width=10, command=self.start_accelerate
        )
        self.accelerate_button.grid(row=2, column=2, padx=10, pady=10, sticky="w")

        # 转换为 GIF（调整到第 4 行）
        self.gif_label = tk.Label(root, text="GIF 分辨率（宽度）：")
        self.gif_label.grid(row=3, column=0, padx=10, pady=10, sticky="e")

        self.gif_entry = tk.Entry(root, width=10)
        self.gif_entry.insert(0, "1080")  # 默认分辨率宽度
        self.gif_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        self.gif_button = tk.Button(
            root, text="转换为 GIF", width=10, command=self.start_gif_conversion
        )
        self.gif_button.grid(row=3, column=2, padx=10, pady=10, sticky="w")

        # 视频压缩（调整到第 5 行）
        self.compress_label = tk.Label(
            root, text="压缩质量（CRF，0-51，越小质量越高）："
        )
        self.compress_label.grid(row=4, column=0, padx=10, pady=10, sticky="e")

        self.compress_entry = tk.Entry(root, width=10)
        self.compress_entry.insert(0, "28")
        self.compress_entry.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        self.compress_button = tk.Button(
            root, text="压缩视频", width=10, command=self.start_compression
        )
        self.compress_button.grid(row=4, column=2, padx=10, pady=10, sticky="w")

        # 裁剪视频（调整到第 6 行）
        self.crop_label = tk.Label(root, text="裁剪视频（开始时间 结束时间，秒）：")
        self.crop_label.grid(row=5, column=0, padx=10, pady=10, sticky="e")

        self.crop_start_entry = tk.Entry(root, width=10)
        self.crop_start_entry.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        self.crop_end_entry = tk.Entry(root, width=10)
        self.crop_end_entry.grid(row=5, column=1, padx=(100, 10), pady=10, sticky="w")

        self.crop_button = tk.Button(
            root, text="裁剪视频", width=10, command=self.start_crop
        )
        self.crop_button.grid(row=5, column=2, padx=10, pady=10, sticky="w")

        # 批量裁剪（第7行）
        self.batch_crop_label = tk.Label(
            root, text="批量裁剪（开始1,结束1,开始2,结束2,...，秒）："
        )
        self.batch_crop_label.grid(row=6, column=0, padx=10, pady=10, sticky="e")
        self.batch_crop_entry = tk.Entry(root, width=40)
        self.batch_crop_entry.grid(row=6, column=1, padx=10, pady=10, sticky="w")
        self.batch_crop_button = tk.Button(
            root, text="批量裁剪", width=10, command=self.start_batch_crop
        )
        self.batch_crop_button.grid(row=6, column=2, padx=10, pady=10, sticky="w")

        # 视频合并（第8行）

        self.merge_label = tk.Label(root, text="合并视频文件夹：")
        self.merge_label.grid(row=7, column=0, padx=10, pady=10, sticky="e")
        self.merge_entry = tk.Entry(root, width=40)
        self.merge_entry.grid(row=7, column=1, padx=10, pady=10, sticky="w")
        self.merge_browse_button = tk.Button(
            root, text="浏览", width=10, command=self.select_merge_folder
        )
        self.merge_browse_button.grid(row=7, column=2, padx=10, pady=10, sticky="w")
        self.merge_out_label = tk.Label(root, text="合并输出文件名：")
        self.merge_out_label.grid(row=8, column=0, padx=10, pady=10, sticky="e")
        self.merge_out_entry = tk.Entry(root, width=40)
        self.merge_out_entry.grid(row=8, column=1, padx=10, pady=10, sticky="w")
        self.merge_button = tk.Button(
            root, text="合并视频", width=10, command=self.start_merge
        )
        self.merge_button.grid(row=8, column=2, padx=10, pady=10, sticky="w")

        # 音频平移（第9行）
        self.shift_audio_label = tk.Label(root, text="音频平移（秒，正为后，负为前）：")
        self.shift_audio_label.grid(row=9, column=0, padx=10, pady=10, sticky="e")
        self.shift_audio_entry = tk.Entry(root, width=10)
        self.shift_audio_entry.grid(row=9, column=1, padx=10, pady=10, sticky="w")
        self.shift_audio_button = tk.Button(
            root, text="音频平移", width=10, command=self.start_shift_audio
        )
        self.shift_audio_button.grid(row=9, column=2, padx=10, pady=10, sticky="w")

    def select_merge_folder(self):
        folder_path = filedialog.askdirectory(title="选择要合并的视频文件夹")
        if folder_path:
            self.merge_entry.delete(0, tk.END)
            self.merge_entry.insert(0, folder_path)
        self.shift_audio_label.grid(row=9, column=0, padx=10, pady=10, sticky="e")
        self.shift_audio_entry = tk.Entry(root, width=10)
        self.shift_audio_entry.grid(row=9, column=1, padx=10, pady=10, sticky="w")
        self.shift_audio_button = tk.Button(
            root, text="音频平移", width=10, command=self.start_shift_audio
        )
        self.shift_audio_button.grid(row=9, column=2, padx=10, pady=10, sticky="w")

    def start_batch_crop(self):
        input_path = self.input_file_entry.get()
        if not self.validate_input_path(input_path):
            return
        output_folder = self.get_output_folder()
        segs = (
            self.batch_crop_entry.get().replace("，", ",").replace("-", ",").split(",")
        )
        try:
            segs = [float(s.strip()) for s in segs if s.strip()]
            if len(segs) % 2 != 0:
                messagebox.showerror("错误", "批量裁剪参数必须成对出现！")
                return
            segments = [(segs[i], segs[i + 1]) for i in range(0, len(segs), 2)]
        except Exception:
            messagebox.showerror("错误", "批量裁剪参数格式错误！")
            return
        if os.path.isfile(input_path):
            input_files = [input_path]
        else:
            input_files = get_video_files(input_path)
        batch_crop_videos(input_files, segments, output_folder)

    def start_merge(self):
        folder = self.merge_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "请先选择要合并的视频文件夹！")
            return
        video_files = get_video_files(folder)
        if not video_files:
            messagebox.showerror("错误", "该文件夹下未找到可合并的视频文件！")
            return
        out_file = self.merge_out_entry.get().strip()
        if not out_file:
            # 自动生成输出文件名
            base = os.path.basename(os.path.normpath(folder))
            out_file = os.path.join(folder, f"{base}_merged_{get_timestamp()}.mp4")
            self.merge_out_entry.insert(0, out_file)
        merge_videos(video_files, out_file)

    def start_shift_audio(self):
        input_path = self.input_file_entry.get()
        if not self.validate_input_path(input_path):
            return
        output_folder = self.get_output_folder()
        try:
            shift = float(self.shift_audio_entry.get())
        except Exception:
            messagebox.showerror("错误", "音频平移参数格式错误！")
            return
        output_path = os.path.join(
            output_folder,
            f"{os.path.splitext(os.path.basename(input_path))[0]}_shift{shift}_{get_timestamp()}.mp4",
        )
        shift_audio(input_path, output_path, shift)

    def start_crop(self):
        input_path = self.input_file_entry.get()
        if not self.validate_input_path(input_path):
            return

        output_folder = self.get_output_folder()
        start_time = float(self.crop_start_entry.get())
        end_time = float(self.crop_end_entry.get())

        if os.path.isfile(input_path):
            # 单个文件处理
            output_path = os.path.join(
                output_folder,
                f"{os.path.splitext(os.path.basename(input_path))[0]}_start{start_time}_end{end_time}_{get_timestamp()}.mp4",
            )
            crop_video(input_path, output_path, start_time, end_time)
        else:
            # 文件夹批量处理
            video_files = get_video_files(input_path)
            for video_file in video_files:
                output_path = os.path.join(
                    output_folder,
                    f"{os.path.splitext(os.path.basename(video_file))[0]}_start{start_time}_end{end_time}_{get_timestamp()}.mp4",
                )
                crop_video(video_file, output_path, start_time, end_time)

    def select_input(self):
        path = filedialog.askopenfilename(
            title="选择视频文件或文件夹",
            filetypes=[("视频文件", "*.mp4 *.mkv *.avi *.mov")],
        )
        if not path:
            path = filedialog.askdirectory(title="选择视频文件夹")
        if path:
            # 去除路径末尾的 *（如果有）
            path = path.rstrip("*").strip()
            self.input_file_entry.delete(0, tk.END)
            self.input_file_entry.insert(0, path)

            # 自动设置输出路径为输入视频文件的路径
            if os.path.isfile(path):
                self.output_folder_entry.delete(0, tk.END)
                self.output_folder_entry.insert(0, os.path.dirname(path))
            elif os.path.isdir(path):
                self.output_folder_entry.delete(0, tk.END)
                self.output_folder_entry.insert(0, path)

    def select_output_folder(self):
        folder_path = filedialog.askdirectory(title="选择输出文件夹")
        if folder_path:
            self.output_folder_entry.delete(0, tk.END)
            self.output_folder_entry.insert(0, folder_path)

    def get_output_folder(self):
        # 如果用户未选择输出文件夹，则使用输入视频文件的路径
        output_folder = self.output_folder_entry.get()
        if not output_folder:
            input_path = self.input_file_entry.get()
            if os.path.isfile(input_path):
                output_folder = os.path.dirname(input_path)
            elif os.path.isdir(input_path):
                output_folder = input_path
            else:
                output_folder = os.getcwd()  # 如果输入路径无效，使用当前工作目录
        return output_folder

    def validate_input_path(self, input_path):
        """验证输入路径是否存在"""
        if not input_path:
            messagebox.showerror("错误", "请输入文件或文件夹路径！")
            return False
        if not os.path.exists(input_path):
            messagebox.showerror("错误", f"路径不存在：{input_path}")
            return False
        return True

    def start_accelerate(self):
        input_path = self.input_file_entry.get()
        if not self.validate_input_path(input_path):
            return

        output_folder = self.get_output_folder()
        speed_factor = float(self.speed_entry.get())

        if os.path.isfile(input_path):
            # 单个文件处理
            output_path = os.path.join(
                output_folder,
                f"{os.path.splitext(os.path.basename(input_path))[0]}_{get_timestamp()}_x{speed_factor}_accelerate.mp4",
            )
            accelerate_video(input_path, output_path, speed_factor)
        else:
            # 文件夹批量处理
            video_files = get_video_files(input_path)
            for video_file in video_files:
                output_path = os.path.join(
                    output_folder,
                    f"{os.path.splitext(os.path.basename(video_file))[0]}_{get_timestamp()}_x{speed_factor}_accelerate.mp4",
                )
                accelerate_video(video_file, output_path, speed_factor)

    def start_gif_conversion(self):
        input_path = self.input_file_entry.get()
        if not self.validate_input_path(input_path):
            return

        output_folder = self.get_output_folder()
        scale = int(self.gif_entry.get())

        if os.path.isfile(input_path):
            # 单个文件处理
            output_path = os.path.join(
                output_folder,
                f"{os.path.splitext(os.path.basename(input_path))[0]}_{get_timestamp()}_{scale}_gif.gif",
            )
            convert_to_gif(input_path, output_path, scale=scale)
        else:
            # 文件夹批量处理
            video_files = get_video_files(input_path)
            for video_file in video_files:
                output_path = os.path.join(
                    output_folder,
                    f"{os.path.splitext(os.path.basename(video_file))[0]}_{get_timestamp()}_{scale}_gif.gif",
                )
                convert_to_gif(video_file, output_path, scale=scale)

    def start_compression(self):
        input_path = self.input_file_entry.get()
        if not self.validate_input_path(input_path):
            return

        output_folder = self.get_output_folder()
        crf = int(self.compress_entry.get())

        if os.path.isfile(input_path):
            # 单个文件处理
            output_path = os.path.join(
                output_folder,
                f"{os.path.splitext(os.path.basename(input_path))[0]}_{get_timestamp()}_crf{crf}_compress.mp4",
            )
            compress_video(input_path, output_path, crf)
        else:
            # 文件夹批量处理
            video_files = get_video_files(input_path)
            for video_file in video_files:
                output_path = os.path.join(
                    output_folder,
                    f"{os.path.splitext(os.path.basename(video_file))[0]}_{get_timestamp()}_crf{crf}_compress.mp4",
                )
                compress_video(video_file, output_path, crf)
