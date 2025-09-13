import pytest

import agent_pilot as ap
from tests.integration.util import has_variables


@pytest.mark.parametrize("task_type", ["DEFAULT", "MULTIMODAL", "DIALOG"])
def test_prompt_generation(get_config, task_type):
    api_key, api_url = get_config

    generated_prompt = ""
    usage = None
    print("Streaming response:")
    for chunk in ap.generate_prompt_stream(
        task_description=f"Write a an email for me of {task_type} task. \
            The prompt is less than 50 words",
        temperature=1.0,
        top_p=0.7,
        model_name="doubao-seed-1.6-250615",
        task_type=task_type,
        api_key=api_key,
        api_url=api_url,
    ):
        # Deal with stream output
        generated_prompt += chunk.data.content
        print(chunk.data.content, end="", flush=True)
        if chunk.event == "usage":
            usage = chunk.data.usage

    print(f"Generated prompt: {str(generated_prompt)}")
    print(f"Usage: {usage}")
    assert generated_prompt is not None
    if task_type in ["DEFAULT", "MULTIMODAL"]:
        assert has_variables(generated_prompt)
    elif task_type in ["DIALOG"]:
        assert not has_variables(generated_prompt) or has_variables(generated_prompt)
    else:
        raise ValueError(f"Unknown task type: {task_type}")
    assert usage is not None
