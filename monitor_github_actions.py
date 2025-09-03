#!/usr/bin/env python3
"""
Мониторинг GitHub Actions workflow
Помогает отслеживать статус сборки и получать уведомления об ошибках
"""

import os
import sys
import time
import json
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class WorkflowRun:
    id: int
    status: str
    conclusion: Optional[str]
    created_at: str
    updated_at: str
    html_url: str
    head_branch: str
    head_sha: str

class GitHubActionsMonitor:
    def __init__(self, repo_owner: str, repo_name: str, token: Optional[str] = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'CNC-Checklist-Monitor'
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
    
    def get_workflow_runs(self, workflow_id: str = "android-release.yml", limit: int = 10) -> List[WorkflowRun]:
        """Получает список запусков workflow"""
        url = f"{self.base_url}/actions/workflows/{workflow_id}/runs"
        params = {'per_page': limit}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            runs = []
            
            for run_data in data.get('workflow_runs', []):
                run = WorkflowRun(
                    id=run_data['id'],
                    status=run_data['status'],
                    conclusion=run_data.get('conclusion'),
                    created_at=run_data['created_at'],
                    updated_at=run_data['updated_at'],
                    html_url=run_data['html_url'],
                    head_branch=run_data['head_branch'],
                    head_sha=run_data['head_sha']
                )
                runs.append(run)
            
            return runs
            
        except requests.RequestException as e:
            print(f"❌ Error fetching workflow runs: {e}")
            return []
    
    def get_run_logs(self, run_id: int) -> Optional[str]:
        """Получает логи конкретного запуска"""
        url = f"{self.base_url}/actions/runs/{run_id}/logs"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
            
        except requests.RequestException as e:
            print(f"❌ Error fetching logs for run {run_id}: {e}")
            return None
    
    def get_run_jobs(self, run_id: int) -> List[Dict]:
        """Получает информацию о джобах в запуске"""
        url = f"{self.base_url}/actions/runs/{run_id}/jobs"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get('jobs', [])
            
        except requests.RequestException as e:
            print(f"❌ Error fetching jobs for run {run_id}: {e}")
            return []
    
    def analyze_run_status(self, run: WorkflowRun) -> Dict:
        """Анализирует статус запуска"""
        status_info = {
            'run_id': run.id,
            'status': run.status,
            'conclusion': run.conclusion,
            'duration': self._calculate_duration(run.created_at, run.updated_at),
            'is_success': run.conclusion == 'success',
            'is_failed': run.conclusion == 'failure',
            'is_running': run.status == 'in_progress',
            'is_queued': run.status == 'queued',
            'url': run.html_url
        }
        
        return status_info
    
    def _calculate_duration(self, created_at: str, updated_at: str) -> str:
        """Вычисляет продолжительность выполнения"""
        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            duration = updated - created
            
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
                
        except Exception:
            return "Unknown"
    
    def print_status_summary(self, runs: List[WorkflowRun]):
        """Выводит сводку по статусам запусков"""
        print("🔍 GitHub Actions Workflow Status")
        print("=" * 60)
        
        if not runs:
            print("❌ No workflow runs found")
            return
        
        for run in runs:
            status_info = self.analyze_run_status(run)
            
            # Иконка статуса
            if status_info['is_success']:
                icon = "✅"
            elif status_info['is_failed']:
                icon = "❌"
            elif status_info['is_running']:
                icon = "🔄"
            elif status_info['is_queued']:
                icon = "⏳"
            else:
                icon = "❓"
            
            print(f"{icon} Run #{run.id}")
            print(f"   Status: {run.status}")
            if run.conclusion:
                print(f"   Conclusion: {run.conclusion}")
            print(f"   Duration: {status_info['duration']}")
            print(f"   Branch: {run.head_branch}")
            print(f"   SHA: {run.head_sha[:8]}")
            print(f"   URL: {run.html_url}")
            print()
    
    def monitor_latest_run(self, check_interval: int = 30):
        """Мониторит последний запуск с заданным интервалом"""
        print(f"🔍 Monitoring latest workflow run (checking every {check_interval}s)")
        print("Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                runs = self.get_workflow_runs(limit=1)
                if not runs:
                    print("❌ No workflow runs found")
                    break
                
                latest_run = runs[0]
                status_info = self.analyze_run_status(latest_run)
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if status_info['is_running']:
                    print(f"[{timestamp}] 🔄 Run #{latest_run.id} is running... ({status_info['duration']})")
                elif status_info['is_queued']:
                    print(f"[{timestamp}] ⏳ Run #{latest_run.id} is queued...")
                elif status_info['is_success']:
                    print(f"[{timestamp}] ✅ Run #{latest_run.id} completed successfully! ({status_info['duration']})")
                    break
                elif status_info['is_failed']:
                    print(f"[{timestamp}] ❌ Run #{latest_run.id} failed! ({status_info['duration']})")
                    print(f"   URL: {latest_run.html_url}")
                    break
                else:
                    print(f"[{timestamp}] ❓ Run #{latest_run.id} status: {latest_run.status}")
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
    
    def download_failed_logs(self, run_id: int, output_dir: str = "logs"):
        """Скачивает логи неудачного запуска"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"📥 Downloading logs for run #{run_id}...")
        
        logs = self.get_run_logs(run_id)
        if logs:
            log_file = os.path.join(output_dir, f"run_{run_id}_logs.txt")
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(logs)
            print(f"✅ Logs saved to: {log_file}")
            
            # Анализируем ошибки
            print("🔍 Analyzing errors...")
            os.system(f"python analyze_errors.py {log_file}")
        else:
            print("❌ Failed to download logs")

def main():
    if len(sys.argv) < 2:
        print("Usage: python monitor_github_actions.py <command> [options]")
        print("Commands:")
        print("  status                    - Show status of recent runs")
        print("  monitor                   - Monitor latest run")
        print("  download <run_id>         - Download logs for specific run")
        print("  analyze <run_id>          - Download and analyze logs")
        print()
        print("Environment variables:")
        print("  GITHUB_TOKEN              - GitHub personal access token")
        print("  GITHUB_REPOSITORY         - Repository in format 'owner/repo'")
        print()
        print("Examples:")
        print("  python monitor_github_actions.py status")
        print("  python monitor_github_actions.py monitor")
        print("  python monitor_github_actions.py download 123456789")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Получаем информацию о репозитории
    repo_env = os.getenv('GITHUB_REPOSITORY', 'MrDanielPotter/CNCChecklist')
    if '/' not in repo_env:
        print("❌ GITHUB_REPOSITORY must be in format 'owner/repo'")
        sys.exit(1)
    
    repo_owner, repo_name = repo_env.split('/', 1)
    
    # Создаем монитор
    monitor = GitHubActionsMonitor(repo_owner, repo_name)
    
    if command == "status":
        runs = monitor.get_workflow_runs(limit=5)
        monitor.print_status_summary(runs)
        
    elif command == "monitor":
        monitor.monitor_latest_run()
        
    elif command == "download":
        if len(sys.argv) < 3:
            print("❌ Run ID required for download command")
            sys.exit(1)
        
        try:
            run_id = int(sys.argv[2])
            monitor.download_failed_logs(run_id)
        except ValueError:
            print("❌ Run ID must be a number")
            sys.exit(1)
            
    elif command == "analyze":
        if len(sys.argv) < 3:
            print("❌ Run ID required for analyze command")
            sys.exit(1)
        
        try:
            run_id = int(sys.argv[2])
            monitor.download_failed_logs(run_id)
        except ValueError:
            print("❌ Run ID must be a number")
            sys.exit(1)
            
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
