"""
Jira API 服务模块

提供 Jira 工单系统集成功能：
- 创建工单
- 查询工单状态
"""

import os
import base64
import httpx
from typing import Optional, List


class JiraService:
    """
    Jira API 服务类

    使用 Jira REST API 进行工单操作。
    """

    def __init__(self):
        self.jira_url = os.getenv("JIRA_URL", "")
        self.api_token = os.getenv("JIRA_API_TOKEN", "")
        self.email = os.getenv("JIRA_EMAIL", "")

    def _get_auth_header(self) -> str:
        """生成 Basic Auth 头"""
        credentials = f"{self.email}:{self.api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium",
        labels: Optional[list] = None
    ) -> dict:
        """
        创建 Jira 工单

        Args:
            project_key: 项目 key（如 "IT"）
            summary: 工单标题
            description: 工单描述
            issue_type: 工单类型（Task/Bug/Story）
            priority: 优先级（Highest/High/Medium/Low/Lowest）
            labels: 标签列表

        Returns:
            包含工单 key 和 ID 的字典

        Raises:
            Exception: API 调用失败时抛出
        """
        if not all([self.jira_url, self.api_token, self.email]):
            raise Exception("Jira 配置不完整，请检查环境变量")

        url = f"{self.jira_url}/rest/api/3/issue"

        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {"name": issue_type},
                "priority": {"name": priority}
            }
        }

        if labels:
            payload["fields"]["labels"] = labels

        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=payload, timeout=30.0)

            if response.status_code != 201:
                raise Exception(f"Jira API 错误: {response.status_code} - {response.text}")

            data = response.json()
            return {
                "key": data["key"],
                "id": data["id"],
                "self": data["self"]
            }

    def get_issue(self, issue_key: str) -> dict:
        """
        获取工单详情

        Args:
            issue_key: 工单 key（如 "IT-123"）

        Returns:
            工单详情字典
        """
        if not all([self.jira_url, self.api_token, self.email]):
            raise Exception("Jira 配置不完整")

        url = f"{self.jira_url}/rest/api/3/issue/{issue_key}"

        headers = {
            "Authorization": self._get_auth_header(),
            "Accept": "application/json"
        }

        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=30.0)

            if response.status_code != 200:
                raise Exception(f"Jira API 错误: {response.status_code}")

            return response.json()

    def transition_issue(self, issue_key: str, transition_name: str) -> bool:
        """
        更新工单状态

        Args:
            issue_key: 工单 key
            transition_name: 转换名称（如 "Done"）

        Returns:
            是否成功
        """
        if not all([self.jira_url, self.api_token, self.email]):
            raise Exception("Jira 配置不完整")

        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json"
        }

        url = f"{self.jira_url}/rest/api/3/issue/{issue_key}/transitions"
        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=30.0)

            if response.status_code != 200:
                return False

            transitions = response.json()["values"]
            for t in transitions:
                if t["name"].lower() == transition_name.lower():
                    transition_url = f"{url}/{t['id']}"
                    resp = client.post(
                        transition_url,
                        headers=headers,
                        json={},
                        timeout=30.0
                    )
                    return resp.status_code == 204

        return False

    def get_issues_by_keys(self, issue_keys: List[str]) -> List[dict]:
        """
        根据 issue key 列表获取工单详情

        Args:
            issue_keys: 工单 key 列表，如 ["SUBV-1", "SUBV-2"]

        Returns:
            工单列表
        """
        if not issue_keys:
            return []

        if not all([self.jira_url, self.api_token, self.email]):
            raise Exception("Jira 配置不完整")

        headers = {
            "Authorization": self._get_auth_header(),
            "Accept": "application/json"
        }

        issues = []
        with httpx.Client() as client:
            for key in issue_keys:
                url = f"{self.jira_url}/rest/api/3/issue/{key}"
                try:
                    response = client.get(url, headers=headers, timeout=30.0)
                    if response.status_code == 200:
                        issue = response.json()
                        issues.append({
                            "key": issue["key"],
                            "summary": issue["fields"]["summary"],
                            "status": issue["fields"]["status"]["name"],
                            "priority": issue["fields"]["priority"]["name"],
                            "updated": issue.get("fields", {}).get("updated", "")
                        })
                except Exception:
                    continue

        return issues


jira_service = JiraService()
