import os
import sys
import tempfile
import time
import schedule

def remove_duplicate_lines_and_keep_order(file_path):
    try:
        seen_lines = set()
        unique_lines = []
        
        with open(file_path, 'r', encoding='utf-8') as infile:
            for line in infile:
                if line not in seen_lines:
                    seen_lines.add(line)
                    unique_lines.append(line)

        temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8')
        temp_file.writelines(unique_lines)
        temp_file.close()

        if os.path.exists(file_path):
            os.remove(file_path)
            
        os.rename(temp_file.name, file_path)
        
        print(f"[{time.ctime()}] 중복 제거가 완료되었습니다. '{file_path}' 파일이 업데이트되었습니다.")

    except FileNotFoundError:
        print(f"[{time.ctime()}] 오류: 파일 '{file_path}'을(를) 찾을 수 없습니다.")
    except Exception as e:
        print(f"[{time.ctime()}] 오류가 발생했습니다: {e}")

def paloalto_edl_deduplicator(dir_or_file_path, param_minutes=5):
    def job():
        if os.path.isfile(dir_or_file_path):
            remove_duplicate_lines_and_keep_order(dir_or_file_path)
        elif os.path.isdir(dir_or_file_path):
            for dirpath, dirnames, filenames in os.walk(dir_or_file_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    remove_duplicate_lines_and_keep_order(file_path)
        else:
            print(f"[{time.ctime()}] 오류: 파일 '{dir_or_file_path}'을(를) 찾을 수 없습니다.")
            sys.exit()

    schedule.every(param_minutes).minutes.do(job)
    print(f"작업 스케줄링을 시작합니다. {param_minutes}분마다 중복 제거가 실행됩니다.")

    while True:
        schedule.run_pending()
        time.sleep(1)

def create_shell_script(filename):
    script_content = """#!/bin/bash

deduplicate_file() {
    local file_path="$1"
    
    if [ ! -f "$file_path" ]; then
        echo "오류: '$file_path'는 유효한 파일이 아닙니다."
        return 1
    fi
    
    echo "처리 중: $file_path"
    
    temp_file=$(mktemp)

    awk '!seen[$0]++' "$file_path" > "$temp_file"
    
    mv "$temp_file" "$file_path"
    
    echo "완료: '$file_path'의 중복이 제거되었습니다."
}

if [ $# -eq 0 ]; then
    echo "사용법: $0 <파일 또는 디렉터리 경로>"
    exit 1
fi

input_path="$1"

if [ -f "$input_path" ]; then
    deduplicate_file "$input_path"
elif [ -d "$input_path" ]; then
    find "$input_path" -type f -print0 | while read -d '' file; do
        deduplicate_file "$file"
    done
else
    echo "오류: 유효한 파일 또는 디렉터리 경로를 입력하세요."
    exit 1
fi
"""

    try:
        with open(filename, 'w', newline='\n') as f:
            f.write(script_content)

        os.chmod(filename, 0o755)

        print(f"'{filename}' 파일이 성공적으로 생성되었습니다.")
        print(f"이제 터미널에서 './{filename} <경로>' 명령어로 실행할 수 있습니다.")
        
    except IOError as e:
        print(f"파일을 저장하는 중 오류가 발생했습니다: {e}")
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")