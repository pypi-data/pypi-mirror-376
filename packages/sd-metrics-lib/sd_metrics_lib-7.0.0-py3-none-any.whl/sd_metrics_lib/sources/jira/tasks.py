from typing import Iterable

from sd_metrics_lib.sources.tasks import TaskProvider


class JiraTaskProvider(TaskProvider):

    def __init__(self,
                 jira_client,
                 query: str,
                 additional_fields: Iterable[str] = None,
                 page_size: int = 1000) -> None:
        self.jira_client = jira_client
        self.query = query.strip()
        self.additional_fields = additional_fields
        if additional_fields is None:
            self._expand_str = None
        else:
            # For Jira, additional_fields correspond to expand values (e.g., 'changelog')
            self._expand_str = ",".join(self.additional_fields)
        self.page_size = max(1, page_size)

    def get_tasks(self):
        tasks = self._fetch_tasks(self.query, self._expand_str)
        if self.additional_fields and 'subtasks' in self.additional_fields:
            self._fetch_child_tasks_and_replace_subtasks_field(tasks)

        return tasks

    def _fetch_tasks(self, query: str, expand_str: str):
        all_tasks = []
        next_page_token = None

        while True:
            result = self.jira_client.enhanced_jql(
                query,
                expand=expand_str,
                limit=self.page_size,
                nextPageToken=next_page_token
            )

            current_tasks = result.get("issues", [])
            if not current_tasks:
                break

            all_tasks.extend(current_tasks)

            next_page_token = result.get('nextPageToken')
            if not next_page_token:
                break

        return all_tasks


    def _fetch_child_tasks_and_replace_subtasks_field(self, jira_tasks: Iterable[dict]):
        if not jira_tasks:
            return

        child_tasks_ids = []
        task_id_to_child_tasks_ids = {}
        for jira_task in jira_tasks:
            subtasks = jira_task.get('fields', {}).get('subtasks', [])
            if subtasks:
                subtasks_ids = [subtask.get('key') for subtask in subtasks if subtask.get('key')]
                if subtasks_ids:
                    child_tasks_ids.extend(subtasks_ids)
                    task_id_to_child_tasks_ids[jira_task['key']] = subtasks_ids

        if not child_tasks_ids:
            return

        child_task_id_to_child_task = self._fetch_tasks_by_id(child_tasks_ids)
        for task in jira_tasks:
            task_key = task['key']
            if task_key in task_id_to_child_tasks_ids:
                task['fields']['subtasks'] = self._create_child_task_list(
                    task_key,
                    task_id_to_child_tasks_ids,
                    child_task_id_to_child_task
                )

    def _fetch_tasks_by_id(self, task_ids):
        query = "key in (" + ", ".join(task_ids) + ")"
        child_tasks = self._fetch_tasks(
            query,
            ",".join([field for field in self.additional_fields if field != 'subtasks'])
        )
        return {task['key']: task for task in child_tasks}

    @staticmethod
    def _create_child_task_list(task_key, task_to_child_tasks_ids, child_task_id_to_child_task):
        return [
            child_task_id_to_child_task[child_key]
            for child_key in task_to_child_tasks_ids[task_key]
            if child_key in child_task_id_to_child_task
        ]

