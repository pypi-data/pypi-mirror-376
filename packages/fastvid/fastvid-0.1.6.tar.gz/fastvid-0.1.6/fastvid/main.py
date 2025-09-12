from fastvid import utils
import tkinter as tk
import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="视频处理工具")
    parser.add_argument(
        "--batch-crop",
        nargs="+",
        metavar=("START", "END"),
        help="批量裁剪，格式: --batch-crop start1 end1 start2 end2 ... (单位秒)",
    )
    parser.add_argument(
        "--merge", nargs="+", help="视频合并，输入多个视频路径，合并为一个视频"
    )
    parser.add_argument("--merge-out", type=str, help="合并输出文件路径")
    parser.add_argument(
        "--shift-audio", type=float, help="音频平移秒数，正数向后，负数向前"
    )
    parser.add_argument("--gui", action="store_true", help="打开 GUI 界面")
    parser.add_argument("--video", type=str, help="输入视频文件或文件夹路径")
    parser.add_argument(
        "--out", type=str, help="输出文件夹路径（默认与输入视频文件路径相同）"
    )
    parser.add_argument(
        "--compress",
        type=int,
        help="压缩视频，设置 CRF 值（0-51，越小质量越高）",
    )
    parser.add_argument(
        "--accelerate",
        type=float,
        help="加速视频，设置加速倍数",
    )
    parser.add_argument("--gif", type=int, help="转换为 GIF，设置分辨率宽度")
    parser.add_argument(
        "--crop",
        nargs=2,
        type=float,
        metavar=("START", "END"),
        help="裁剪视频，设置开始时间和结束时间（秒）",
    )

    args = parser.parse_args()

    if args.gui:
        root = tk.Tk()
        utils.VideoToolApp(root)
        root.mainloop()
    else:
        did_any = False
        # 合并
        if args.merge is not None:
            if not args.merge_out:
                print("错误：合并操作需要 --merge-out 指定输出文件路径")
            else:
                utils.merge_videos(args.merge, args.merge_out)
                did_any = True

        # 其他操作需要 --video
        if (
            args.crop is not None
            or args.batch_crop is not None
            or args.shift_audio is not None
            or args.compress is not None
            or args.accelerate is not None
            or args.gif is not None
        ):
            if not args.video:
                print("错误：未指定输入视频文件或文件夹路径。")
                parser.print_help()
                return

            # 如果未指定输出路径，则默认使用输入视频文件的路径
            if not args.out:
                if os.path.isfile(args.video):
                    args.out = os.path.dirname(args.video)
                elif os.path.isdir(args.video):
                    args.out = args.video
                else:
                    print("错误：输入路径无效。")
                    parser.print_help()
                    return

            # 普通裁剪
            if args.crop is not None:
                start_time, end_time = args.crop
                output_path = os.path.join(
                    args.out, f"cropped_{utils.get_timestamp()}.mp4"
                )
                utils.crop_video(args.video, output_path, start_time, end_time)
                did_any = True
            # 批量裁剪
            if args.batch_crop is not None:
                if len(args.batch_crop) % 2 != 0:
                    print("错误：--batch-crop 参数必须成对出现 (start end)")
                else:
                    segments = [
                        (float(args.batch_crop[i]), float(args.batch_crop[i + 1]))
                        for i in range(0, len(args.batch_crop), 2)
                    ]
                    input_files = (
                        [args.video]
                        if os.path.isfile(args.video)
                        else utils.get_video_files(args.video)
                    )
                    utils.batch_crop_videos(input_files, segments, args.out)
                    did_any = True
            # 音频平移
            if args.shift_audio is not None:
                output_path = os.path.join(
                    args.out, f"shifted_{utils.get_timestamp()}.mp4"
                )
                utils.shift_audio(args.video, output_path, args.shift_audio)
                did_any = True
            # 其他功能
            if args.compress is not None:
                output_path = os.path.join(
                    args.out, f"compressed_{utils.get_timestamp()}.mp4"
                )
                utils.compress_video(args.video, output_path, args.compress)
                did_any = True
            if args.accelerate is not None:
                output_path = os.path.join(
                    args.out, f"accelerated_{utils.get_timestamp()}.mp4"
                )
                utils.accelerate_video(args.video, output_path, args.accelerate)
                did_any = True
            if args.gif is not None:
                output_path = os.path.join(
                    args.out, f"converted_{utils.get_timestamp()}.gif"
                )
                utils.convert_to_gif(args.video, output_path, scale=args.gif)
                did_any = True
        if not did_any:
            print(
                "错误：未指定操作类型（--compress, --accelerate, --gif, --crop, --batch-crop, --merge, --shift-audio）。"
            )
            parser.print_help()


if __name__ == "__main__":
    main()
