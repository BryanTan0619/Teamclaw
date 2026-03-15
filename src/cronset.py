import json
import subprocess
import sys

def import_cron_jobs(input_file="cron_backup.json"):
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        for job in jobs:
            print(f"[*] 正在尝试在新设备恢复任务: {job['name']}")
            
            # 构建新设备的 add 指令
            # 即使 ID 不同，只要 --agent "test2" 名字对上即可
            cmd = [
                "openclaw", "cron", "add",
                "--name", job["name"],
                "--agent", job["agentId"],
                "--session-key", job["sessionKey"],
                "--session", job.get("session") or "isolated",
                "--tz", job.get("tz") or "Asia/Shanghai",
                "--cron", job["cron"],
                "--message", job["message"]
            ]
            
            # 处理不推送模式
            if job.get("mode") == "none":
                cmd.append("--no-deliver")

            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"    [成功] 任务 '{job['name']}' 已重新挂载到 Agent: {job['agentId']}")
            else:
                print(f"    [失败] 任务 '{job['name']}': {result.stderr.strip()}")

    except FileNotFoundError:
        print(f"[!] 错误：找不到文件 {input_file}")
    except Exception as e:
        print(f"[!] 恢复过程中出现异常: {e}")

if __name__ == "__main__":
    import_cron_jobs()