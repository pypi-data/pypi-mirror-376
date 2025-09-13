import pytest

import agent_pilot as ap

from typing import List

from agent_pilot.models import PromptVersion
from agent_pilot.eval.models import Metric


@pytest.mark.parametrize("task_type", ["DEFAULT", "MULTIMODAL", "DIALOG"])
def test_create_task_and_list_prompts_and_get_prompt_and_get_metric(get_config, task_type):
    api_key, api_url = get_config
    print("Creating a task....")
    prompt_version: PromptVersion = ap.create_task(
        name=f"{task_type}_test_task",
        task_type=task_type,
        prompt="This is a prompt that contains two variables: {{variable_1}} and {{variable_2}}",
        variable_types=None,
        model_name="doubao-seed-1.6-250615",
        criteria="This is a test criteria",
        api_key=api_key,
        api_url=api_url,
    )
    print(f"Task with {prompt_version.task_id} is created.")
    print(f"Details = {prompt_version}")
    assert prompt_version.task_id is not None
    assert prompt_version.version == "v1"
    assert prompt_version.prompt == "This is a prompt that contains two variables: {{variable_1}} and {{variable_2}}"
    assert prompt_version.criteria == "This is a test criteria"
    assert prompt_version.variable_names == ["variable_1", "variable_2"]
    assert prompt_version.model_name == "doubao-seed-1.6-250615"
    assert prompt_version.temperature == 1.0
    assert prompt_version.top_p == 0.7
    print(f"Login your PromptPilot to see the task: {prompt_version.task_id}")

    print(f"List prompts of {prompt_version.task_id}")
    prompt_versions: List[PromptVersion] = ap.list_prompts(
        task_id=prompt_version.task_id, api_key=api_key, api_url=api_url
    )
    assert len(prompt_versions) == 1
    assert prompt_versions[0] == prompt_version

    print(f"Getting a prompt version by task_id={prompt_version.task_id} and version={prompt_version.version}....")
    prompt_version_by_get = ap.get_prompt(
        task_id=prompt_version.task_id, version=prompt_version.version, api_key=api_key, api_url=api_url
    )
    assert prompt_version_by_get == prompt_version

    print(f"Getting the metric of {prompt_version.task_id} and version={prompt_version.version}")
    metric = ap.get_metric(
        task_id=prompt_version.task_id, version=prompt_version.version, api_key=api_key, api_url=api_url
    )
    assert metric == Metric(**{"criteria": "This is a test criteria"})
