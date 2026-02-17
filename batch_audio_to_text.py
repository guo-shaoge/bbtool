import os
import subprocess
from pathlib import Path

# ===== 配置区域 =====
ROOT_DIR = "./downloads/eng_only_audio"
OUTPUT_DIR = "./downloads/eng_only_audio_text"
TRANSCRIBE_SCRIPT = "audio_to_text.py"
# ====================

os.makedirs(OUTPUT_DIR, exist_ok=True)

def find_p1_files(root):
    p1_files = []
    for path in Path(root).rglob("*[P1]*.m4a"):
        if "[P1]" in path.name:
            p1_files.append(path)
    return p1_files


def main():
    files = find_p1_files(ROOT_DIR)
    print(f"Found {len(files)} P1 files")

    for file_path in files:
        # 用目录名作为输出文件名
        parent_name = file_path.parent.name
        output_txt = Path(OUTPUT_DIR) / f"{parent_name}.txt"

        if output_txt.exists():
            print(f"Skip (already exists): {output_txt}")
            continue

        print(f"\nProcessing: {file_path}")

        try:
            result = subprocess.run(
                ["python", TRANSCRIBE_SCRIPT, str(file_path)],
                capture_output=True,
                text=True,
                check=True
            )

            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(result.stdout)

            print(f"Saved to: {output_txt}")

        except subprocess.CalledProcessError as e:
            print(f"Error processing {file_path}")
            print(e.stderr)


if __name__ == "__main__":
    main()

