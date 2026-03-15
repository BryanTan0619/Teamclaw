import subprocess
import json
import sys

def export_cron_jobs(output_file="cron_backup.json"):
    try:
        # 修正：将 capture_data 改为 capture_output
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        jobs = data.get("jobs", [])

        clean_jobs = []
        for job in jobs:
            # 提取核心逻辑参数
            clean_job = {
                "name": job.get("name"),
                "agentId": job.get("agentId"),
                "sessionKey": job.get("sessionKey"),
                "cron": job.get("schedule", {}).get("expr"),
                "tz": job.get("schedule", {}).get("tz"),
                "message": job.get("payload", {}).get("message"),
                "session": job.get("sessionTarget"),
                "mode": job.get("delivery", {}).get("mode")
            }
            clean_jobs.append(clean_job)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(clean_jobs, f, indent=2, ensure_ascii=False)
        
        print(f"[*] 成功从当前设备导出 {len(clean_jobs)} 个任务到 {output_file}")

    except Exception as e:
        print(f"[!] 导出失败: {e}", file=sys.stderr)

if __name__ == "__main__":
    export_cron_jobs()