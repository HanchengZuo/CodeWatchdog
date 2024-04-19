import os
import sys
import time
import difflib
import subprocess
import hashlib
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# def analyze_file_with_flake8(file_path):
#     """对文件执行flake8静态分析，并返回结果。"""
#     result = subprocess.run(['flake8', file_path, '--format=%(row)d:%(text)s'], capture_output=True, text=True)
#     return result.stdout

# def filter_flake8_results(flake8_results, added_line_numbers):
#     """根据新增代码的行号过滤flake8的结果。"""
#     relevant_results = []
#     for line in flake8_results.split('\n'):
#         if line:
#             line_number = int(line.split(':')[0])  # 修改这里以正确解析行号
#             if line_number in added_line_numbers:
#                 relevant_results.append(line)
#     return relevant_results

# def get_added_line_numbers(diff):
#     """从diff中获取新增行的行号。"""
#     added_line_numbers = []
#     line_number = None
#     for line in diff:
#         if line.startswith('@@'):
#             line_number = int(line.split()[2].split(',')[0].lstrip('+'))  # 解析当前区块的起始行号
#         elif line.startswith('+') and not line.startswith('+++'):
#             if line_number is not None:
#                 added_line_numbers.append(line_number)
#             line_number += 1
#     return added_line_numbers

class MyHandler(FileSystemEventHandler):
    def __init__(self, directory, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_contents = {}  # 用于存储文件的实际内容
        self.file_contents_hash = {}  # 用于存储文件内容的哈希值
        self.preload_file_contents(directory)


    def preload_file_contents(self, directory):
        """遍历指定目录，预加载所有.py文件的内容并计算哈希值"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        contents = f.readlines()
                        self.file_contents[file_path] = contents  # 存储文件内容
                        self.file_contents_hash[file_path] = self.compute_hash(contents)  # 存储内容哈希值

    def compute_hash(self, contents):
        """计算文件内容的MD5哈希值，忽略行尾空白和空行"""
        md5 = hashlib.md5()
        for line in contents:
            processed_line = line.rstrip()  # 移除行尾空白字符
            if processed_line:  # 忽略空行
                md5.update(processed_line.encode('utf-8'))
        return md5.hexdigest()
    
    def read_lines_from_file(self, filepath, line_numbers):
        """根据给定的行号从文件中读取内容"""
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # 提取特定行号的内容，注意列表索引从0开始，行号从1开始
        selected_lines = [lines[i-1] for i in line_numbers if 0 < i <= len(lines)]
        return selected_lines

    def on_modified(self, event):
        if event.src_path.endswith('.py'):

            try:
                with open(event.src_path, 'r', encoding='utf-8') as file:
                    new_contents = file.readlines()
            except IOError as e:
                print(f"Error opening file: {e}")
                return
            
            new_hash = self.compute_hash(new_contents)
            old_hash = self.file_contents_hash.get(event.src_path, '')

            if new_hash != old_hash:
                self.file_contents_hash[event.src_path] = new_hash
                self.file_contents[event.src_path] = new_contents
                
                old_contents = self.file_contents.get(event.src_path, [])  # 获取旧版本内容
                diff = difflib.unified_diff(old_contents, new_contents, fromfile='before.py', tofile='after.py', lineterm='', n=0)
                added_lines = [line for line in diff if line.startswith('+') and not line.startswith('+++')]

                current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if added_lines:
                    print(f'[{current_time_str}] Detected new content in the file: [{event.src_path}]')

                    diff = list(difflib.ndiff(old_contents, new_contents))
                    added_line_numbers = [i+1 for i, line in enumerate(diff) if line.startswith('+ ')]

                    for line_no in added_line_numbers:
                        print(f"New line at {line_no}")
                        
                else:
                    print(f"File {event.src_path} modified but no new content detected.")
                
                # if added_lines:
                #     current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                #     print(f'[{current_time}] Detected potential AI-generated code in the following file: [{event.src_path}]')
                    
                #     # Adjust printing based on the number of added lines
                #     if len(added_lines) > 6:
                #         for line in added_lines[:3]:
                #             if line.startswith('+'):
                #                 print(line[1:].rstrip())  # Remove the '+' at the beginning of the line.
                #         print("\n...\n")
                #         for line in added_lines[-3:]:
                #             if line.startswith('+'):
                #                 print(line[1:].rstrip())  # Remove the '+' at the beginning of the line.
                #     else:
                #         for line in added_lines:
                #             if line.startswith('+'):
                #                 print(line[1:].rstrip())  # Print all lines if 6 or fewer changes
                # else:
                #     print(f"File {event.src_path} modified but no new content detected.")

                # added_line_numbers = get_added_line_numbers(diff)
                # print("\nAdded line numbers:")
                # print(added_line_numbers)
                # flake8_results = analyze_file_with_flake8(event.src_path)
                # relevant_results = filter_flake8_results(flake8_results, added_line_numbers)

                # if relevant_results:
                #     print("Relevant flake8 issues related to AI-generated code:")
                #     for result in relevant_results:
                #         print(result)
                # else:
                #     print("No relevant flake8 issues detected related to AI-generated code.")

                # # Run flake8 analysis on the whole file
                # flake8_results = analyze_file_with_flake8(event.src_path)
                # print("\nflake8 analysis results:")
                # print(flake8_results)

            else:
                print(f"File {event.src_path} modified but no content change detected based on hash.")
                return
            
            

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else '.'

    if not os.path.isdir(path):
        print("The provided path is not a directory.")
        sys.exit(1)

    event_handler = MyHandler(path)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()