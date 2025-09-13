import agent_pilot as ap


def test_evaluation(get_config):
    api_key, api_url = get_config

    example = {
        "example_id": "ex_id_1",  # optional
        "prompt": "This is a prompt template with {{variable_1}} and {{variable_2}}.",
        "variables": {
            "variable_1": "content of variable 1",
            "variable_2": "content of variable 2",
        },
        "response": "The model answer",
        "reference": "The reference answer",  # optional, used for compare against the model answer in criteria.
    }

    metric = {"criteria": "The model answer should be the same as the reference answer."}

    print("Evaluating the example...")
    print(f"example = {example}")
    print(f"metric = {metric}")
    result = ap.eval.evaluate(
        example=example,
        metric=metric,
        api_key=api_key,
        api_url=api_url,
    )

    assert isinstance(result.score, int) and result.score >= 1 and result.score <= 5
    assert isinstance(result.analysis, str) and len(result.analysis) >= 0
    assert isinstance(result.confidence, float) and result.confidence >= 0 and result.confidence <= 1
    assert result.example_id == example["example_id"]
    assert result.reference == example["reference"]
