import pytest
import requests
from unittest.mock import patch, MagicMock

from agent_pilot.eval.eval_client import eval_service_input_response_evaluate, eval_service_criteria_generation
from agent_pilot.config import config as actual_global_config
from agent_pilot.eval.models import Metric, InputResponseExample, EvaluationDataExample


# --- Fixtures ---
@pytest.fixture
def mock_get_config(monkeypatch):
    """
    Fixture to configure the global agent_pilot.config.config instance for tests.
    It sets default values suitable for 'production' mode tests.
    Test functions can further modify this global config using monkeypatch if needed.
    """

    # Set values for 'production' mode tests
    monkeypatch.setattr(actual_global_config, "api_key", "test_api_key_from_config")
    monkeypatch.setattr(actual_global_config, "api_url", "http://default-api-url.com")

    monkeypatch.setattr(actual_global_config, "local_debug", False)
    monkeypatch.setattr(actual_global_config, "verbose", False)  # Default verbose to False for tests
    monkeypatch.setattr(actual_global_config, "ssl_verify", True)  # Default ssl_verify for tests

    yield actual_global_config  # Provide the configured global instance to tests


@pytest.fixture
def mock_requests_post():
    """Fixture to mock requests.post."""
    with patch("agent_pilot.http_client.requests.post") as mock_post:
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.ok = True
        # Default successful response structure, ensure EvaledDataExample is present
        mock_response.json.return_value = {
            "Result": {
                "EvaledDataExample": {
                    "example_id": "ex_1",
                    "messages": [{"role": "user", "content": "input"}],
                    "response": [{"role": "assistant", "content": "response"}],
                    "score": 5,
                    "analysis": "Good response",
                    "confidence": 0.9,
                    "reference": [{"role": "assistant", "content": "expected response"}],
                }
            }
        }
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def example_input_response_payload_data():
    """Sample input_response_sample data as a dictionary, representing the expected payload."""
    return {
        "example_id": "ex_1",
        "messages": [{"role": "user", "content": "input"}],
        "response": [{"role": "assistant", "content": "response"}],
    }


@pytest.fixture
def example_input_response(example_input_response_payload_data):
    """
    Mocked InputResponseExample object that simulates the
    to_evaluation_data().model_dump() chain.
    """
    mock_eval_data_instance = MagicMock()
    mock_eval_data_instance.model_dump.return_value = example_input_response_payload_data

    mock_input_response_example_instance = MagicMock()
    mock_input_response_example_instance.to_evaluation_data.return_value = mock_eval_data_instance
    return mock_input_response_example_instance


@pytest.fixture
def sample_metric_template():
    """Sample metric_prompt_template data as a Metric instance."""
    return Metric(criteria="Is the response accurate?")  # Return Metric instance


# --- Test Cases ---


def test_evaluate_success_production(
    mock_get_config,
    mock_requests_post,
    example_input_response,
    sample_metric_template,
    example_input_response_payload_data,
    monkeypatch,
):
    """Test successful evaluation in production mode."""

    custom_api_key = "test_api_key_from_args"
    custom_api_url = "http://default-api-url.com"
    # Mock the API response for this specific test to ensure EvaluationResult can be formed
    mock_response_json = {
        "Result": {
            "evaled_data_example": {
                "example_id": "ex_1",
                "messages": [{"role": "user", "content": "input"}],
                "response": [{"role": "assistant", "content": "response"}],
                "score": 5,
                "analysis": "Good response",
                "confidence": 0.9,
                "reference": [{"role": "assistant", "content": "expected response"}],
            }
        }
    }
    mock_requests_post.return_value.json.return_value = mock_response_json

    result = eval_service_input_response_evaluate(
        input_response_example=example_input_response,
        metric_prompt=sample_metric_template,
        api_url=custom_api_url,
        api_key=custom_api_key,
    )

    assert result.score == 5
    assert result.example_id == "ex_1"
    mock_requests_post.assert_called_once()
    args, kwargs = mock_requests_post.call_args
    assert kwargs["url"].startswith(custom_api_url)
    # URL path should be for production because local_debug is False
    assert "/agent-pilot?Version=2024-01-01&Action=EvalServiceInputResponseEvaluate" in kwargs["url"]
    assert "Authorization" in kwargs["headers"]
    assert kwargs["headers"]["Authorization"] == f"Bearer {custom_api_key}"
    assert kwargs["json"]["EvalDataExample"] == example_input_response_payload_data
    assert kwargs["json"]["MetricPrompt"] == sample_metric_template.model_dump()


def test_evaluate_success_local_debug(
    mock_get_config,
    mock_requests_post,
    example_input_response,
    sample_metric_template,
    example_input_response_payload_data,
    monkeypatch,
):
    """Test successful evaluation in local debug mode."""
    # mock_get_config fixture initially sets global config for production.
    # Modify it for local debug mode for this test.
    monkeypatch.setattr(mock_get_config, "api_url", "http://localhost:8080")  # A typical local debug URL
    monkeypatch.setattr(mock_get_config, "local_debug", True)
    monkeypatch.setattr(mock_get_config, "api_key", None)  # API key might be None or different for local debug

    # Mock the API response
    mock_response_json = {
        "Result": {
            "evaled_data_example": {
                "example_id": "ex_1",
                "messages": [{"role": "user", "content": "input"}],
                "response": [{"role": "assistant", "content": "response"}],
                "score": 5,
                "analysis": "Good response",
                "confidence": 0.9,
                "reference": [{"role": "assistant", "content": "expected response"}],
            }
        }
    }
    mock_requests_post.return_value.json.return_value = mock_response_json

    result = eval_service_input_response_evaluate(
        input_response_example=example_input_response, metric_prompt=sample_metric_template, api_key="test_api_key"
    )

    assert result.score == 5
    assert result.example_id == "ex_1"
    mock_requests_post.assert_called_once()
    args, kwargs = mock_requests_post.call_args
    # http_client should use the globally configured api_url and local_debug state
    # assert call_args[0][0].startswith(mock_get_config.api_url)  # Checks against 'http://localhost:8080'
    # URL path should be for local_debug because local_debug is True
    assert "/agent-pilot?Version=2024-01-01&Action=EvalServiceInputResponseEvaluate" in kwargs["url"]
    assert "Authorization" in kwargs["headers"]
    assert kwargs["json"]["EvalDataExample"] == example_input_response_payload_data
    assert kwargs["json"]["MetricPrompt"] == sample_metric_template.model_dump()


def test_evaluate_missing_api_key_production(
    mock_get_config, mock_requests_post, example_input_response, sample_metric_template, monkeypatch
):
    """Test RuntimeError when API key is missing in production."""
    # Configure global config for this specific scenario
    monkeypatch.setattr(mock_get_config, "api_key", None)
    monkeypatch.setattr(mock_get_config, "local_debug", False)  # Ensure production mode path construction
    monkeypatch.setattr(mock_get_config, "api_url", "http://default-api-url.com")

    # Simulate http_client.post raising the error due to missing API key in production
    # This side_effect simulates the behavior within http_client.post when it detects this condition
    mock_requests_post.side_effect = RuntimeError("No authentication api_key provided")

    with pytest.raises(RuntimeError, match="No authentication api_key provided"):
        eval_service_input_response_evaluate(
            input_response_example=example_input_response, metric_prompt=sample_metric_template, api_key="test_api_key"
        )
    # Depending on how http_client checks, post might be called or not.
    # If the check is inside http_client.post before requests.post, it's called once.
    mock_requests_post.assert_called_once()


def test_evaluate_unauthorized_401(mock_get_config, mock_requests_post, example_input_response, sample_metric_template):
    """Test RuntimeError on 401 Unauthorized response."""
    mock_response = mock_requests_post.return_value
    mock_response.status_code = 401

    with pytest.raises(RuntimeError, match="Invalid or unauthorized API credentials"):
        eval_service_input_response_evaluate(
            input_response_example=example_input_response, metric_prompt=sample_metric_template, api_key="test_api_key"
        )
    mock_requests_post.assert_called_once()


def test_evaluate_other_http_error(mock_get_config, mock_requests_post, example_input_response, sample_metric_template):
    """Test RuntimeError on non-200/401 HTTP error."""
    mock_response = mock_requests_post.return_value
    mock_response.status_code = 500

    mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Error decoding JSON", "doc", 0)
    mock_response.text = "Internal Server Error Text"

    with pytest.raises(RuntimeError, match=r"Network error while fetching evaluation results:"):
        eval_service_input_response_evaluate(
            input_response_example=example_input_response, metric_prompt=sample_metric_template, api_key="test_api_key"
        )
    mock_requests_post.assert_called_once()


def test_evaluate_network_error(mock_get_config, mock_requests_post, example_input_response, sample_metric_template):
    """Test RuntimeError on network error."""
    mock_requests_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")

    with pytest.raises(RuntimeError, match=r"Network error while fetching evaluation results:.*Failed to connect.*"):
        eval_service_input_response_evaluate(
            input_response_example=example_input_response, metric_prompt=sample_metric_template, api_key="test_api_key"
        )
    mock_requests_post.assert_called_once()


def test_evaluate_empty_result(mock_get_config, mock_requests_post, example_input_response, sample_metric_template):
    """Test RuntimeError when API returns 'EvaledDataExample' as None or missing."""
    mock_response = mock_requests_post.return_value
    mock_response.status_code = 200
    # Simulate 'EvaledDataExample' being missing or None in the 'Result'
    mock_response.json.return_value = {"Result": {"evaled_data_example": None}}

    # This will cause TypeError: EvaluationDataExample.__init__() keywords must be strings
    # which is caught and re-raised.
    with pytest.raises(RuntimeError, match=r"Error fetching or processing evaluation results:"):
        eval_service_input_response_evaluate(
            input_response_example=example_input_response, metric_prompt=sample_metric_template, api_key="test_api_key"
        )
    mock_requests_post.assert_called_once()

    # Test case for when 'Result' itself is empty or missing
    mock_requests_post.reset_mock()
    mock_response.json.return_value = {}  # Result is missing
    with pytest.raises(RuntimeError, match="Evaluation results not found in API response"):
        eval_service_input_response_evaluate(
            input_response_example=example_input_response, metric_prompt=sample_metric_template, api_key="test_api_key"
        )
    mock_requests_post.assert_called_once()


def test_evaluate_custom_api_key_url(
    mock_get_config,
    mock_requests_post,
    example_input_response,
    sample_metric_template,
    example_input_response_payload_data,
    monkeypatch,  # Add monkeypatch
):
    """Test using custom api_key and api_url passed as arguments."""
    custom_key = "custom_test_key"
    custom_url = "http://custom-api-url.com"

    # Even if global config is set one way, passed args should override.
    # The http_client should prioritize args passed to its constructor/methods.
    # Let's ensure global config is different to prove args take precedence.
    monkeypatch.setattr(mock_get_config, "api_key", "global_key_should_be_ignored")
    monkeypatch.setattr(mock_get_config, "api_url", "http://global-url.com_should_be_ignored")
    monkeypatch.setattr(mock_get_config, "local_debug", False)  # Assume custom URL is not local debug unless specified

    mock_response_json = {
        "Result": {
            "evaled_data_example": {
                "example_id": "ex_1",
                "messages": [{"role": "user", "content": "input"}],
                "response": [{"role": "assistant", "content": "response"}],
                "score": 5,
                "analysis": "Good response",
                "confidence": 0.9,
                "reference": [{"role": "assistant", "content": "expected response"}],
            }
        }
    }
    mock_requests_post.return_value.json.return_value = mock_response_json

    result = eval_service_input_response_evaluate(
        input_response_example=example_input_response,
        metric_prompt=sample_metric_template,
        api_key=custom_key,  # Pass custom key
        api_url=custom_url,  # Pass custom URL
    )

    assert result.score == 5
    mock_requests_post.assert_called_once()
    args, kwargs = mock_requests_post.call_args
    assert kwargs["url"].startswith(custom_url)
    assert "Authorization" in kwargs["headers"]
    assert kwargs["headers"]["Authorization"] == f"Bearer {custom_key}"
    assert kwargs["json"]["EvalDataExample"] == example_input_response_payload_data
    assert kwargs["json"]["MetricPrompt"] == sample_metric_template.model_dump()


def test_input_response_example():
    # Test with messages -- plain text
    example = InputResponseExample(
        example_id="ex_1",
        messages=[
            {"role": "system", "content": "system input"},
            {"role": "user", "content": "user input"},
        ],
        response="response",
        reference="expected response",
        score=4,
        analysis="Good response",
        confidence=0.9,
    )
    assert example.to_evaluation_data() == EvaluationDataExample(
        example_id="ex_1",
        messages=[
            {"role": "system", "content": "system input"},
            {"role": "user", "content": "user input"},
        ],
        response=[{"role": "assistant", "content": "response"}],
        reference=[{"role": "assistant", "content": "expected response"}],
        score=4,
        analysis="Good response",
        confidence=0.9,
    )

    # Test without example id -- plain text
    example = InputResponseExample(
        messages=[
            {"role": "system", "content": "system input"},
            {"role": "user", "content": "user input"},
        ],
        response="response",
        reference="expected response",
        score=4,
        analysis="Good response",
        confidence=0.9,
    )
    assert example.to_evaluation_data() == EvaluationDataExample(
        messages=[
            {"role": "system", "content": "system input"},
            {"role": "user", "content": "user input"},
        ],
        response=[{"role": "assistant", "content": "response"}],
        reference=[{"role": "assistant", "content": "expected response"}],
        score=4,
        analysis="Good response",
        confidence=0.9,
    )

    # Test with messages -- image_url
    example = InputResponseExample(
        example_id="ex_1",
        messages=[
            {"role": "system", "content": "system input"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "user input 1st part"},
                    {"type": "image_url", "image_url": {"url": "https://www.image.com/1.jpg"}},
                    {"type": "text", "text": "user input 2nd part"},
                ],
            },
        ],
        response="response",
        reference="expected response",
        score=4,
        analysis="Good response",
        confidence=0.9,
    )
    assert example.to_evaluation_data() == EvaluationDataExample(
        example_id="ex_1",
        messages=[
            {"role": "system", "content": "system input"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "user input 1st part"},
                    {"type": "image_url", "image_url": {"url": "https://www.image.com/1.jpg"}},
                    {"type": "text", "text": "user input 2nd part"},
                ],
            },
        ],
        response=[{"role": "assistant", "content": "response"}],
        reference=[{"role": "assistant", "content": "expected response"}],
        score=4,
        analysis="Good response",
        confidence=0.9,
    )

    # Test with input -- plain text
    example = InputResponseExample(
        example_id="ex_1",
        input="this is the rendered input, which is a sophisticated string",
        response="response",
        reference="expected response",
        score=4,
        analysis="Good response",
        confidence=0.9,
    )
    assert example.to_evaluation_data() == EvaluationDataExample(
        example_id="ex_1",
        messages=[{"role": "user", "content": "this is the rendered input, which is a sophisticated string"}],
        response=[{"role": "assistant", "content": "response"}],
        reference=[{"role": "assistant", "content": "expected response"}],
        score=4,
        analysis="Good response",
        confidence=0.9,
    )

    # Test with prompt and variables -- plain text
    example = InputResponseExample(
        example_id="ex_1",
        prompt="this is the prompt, with {{var1}} and {{var2}}",
        variables={"var1": "value1", "var2": "value2"},
        response="response",
        reference="expected response",
        score=4,
        analysis="Good response",
        confidence=0.9,
    )
    assert example.to_evaluation_data() == EvaluationDataExample(
        example_id="ex_1",
        messages=[{"role": "user", "content": "this is the prompt, with value1 and value2"}],
        response=[{"role": "assistant", "content": "response"}],
        reference=[{"role": "assistant", "content": "expected response"}],
        score=4,
        analysis="Good response",
        confidence=0.9,
    )

    # Test with prompt and variables -- image_url
    example = InputResponseExample(
        example_id="ex_1",
        prompt="this is the prompt, with {{var1}} and {{var2}}",
        variables={
            "var1": {"type": "text", "value": "text value1"},
            "var2": {"type": "image_url", "value": "https://www.image.com/1.jpg"},
        },
        response="response",
        reference="expected response",
        score=4,
        analysis="Good response",
        confidence=0.9,
    )
    assert example.to_evaluation_data() == EvaluationDataExample(
        example_id="ex_1",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "this is the prompt, with "},
                    {"type": "text", "text": "text value1"},
                    {"type": "text", "text": " and "},
                    {"type": "image_url", "image_url": {"url": "https://www.image.com/1.jpg"}},
                ],
            },
        ],
        response=[{"role": "assistant", "content": "response"}],
        reference=[{"role": "assistant", "content": "expected response"}],
        score=4,
        analysis="Good response",
        confidence=0.9,
    )


@pytest.fixture
def sample_input_response_examples():
    """Provides a list of sample InputResponseExample objects for testing."""
    return [
        InputResponseExample(
            example_id="ex_1",
            messages=[{"role": "user", "content": "What is the capital of France?"}],
            response="Paris is the capital of France.",
        ),
        InputResponseExample(
            example_id="ex_2", messages=[{"role": "user", "content": "What is 2 + 2?"}], response="2 + 2 equals 4."
        ),
    ]


class TestEvalServiceCriteriaGeneration:
    @patch("agent_pilot.eval.eval_client.get_http_client")
    def test_criteria_generation_success(self, mock_get_http_client, sample_input_response_examples):
        """Test successful criteria generation."""
        mock_client = MagicMock()
        mock_get_http_client.return_value = mock_client

        expected_criteria = "The response should be accurate and concise."
        api_response_data = {"Result": {"generated_criteria": expected_criteria}}
        mock_client.post.return_value = (api_response_data, 200)

        result = eval_service_criteria_generation(sample_input_response_examples, api_key="test_key")

        assert result == expected_criteria
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args[1]
        assert call_args["action"] == "EvalServiceCriteriaGeneration"
        assert len(call_args["data"]["EvalDataExamples"]) == 2
        assert call_args["data"]["EvalDataExamples"][0]["example_id"] == "ex_1"

    def test_criteria_generation_with_empty_list(self):
        """Test calling with an empty list of examples raises ValueError."""
        with pytest.raises(ValueError, match="input_response_examples must be provided and cannot be empty."):
            eval_service_criteria_generation([])

    @patch("agent_pilot.eval.eval_client.get_http_client")
    def test_criteria_generation_unauthorized(self, mock_get_http_client, sample_input_response_examples):
        """Test handling of 401 unauthorized response."""
        mock_client = MagicMock()
        mock_get_http_client.return_value = mock_client
        mock_client.post.return_value = ({"error": "unauthorized"}, 401)

        with pytest.raises(RuntimeError, match="Invalid or unauthorized API credentials"):
            eval_service_criteria_generation(sample_input_response_examples, api_key="test_key")

    @patch("agent_pilot.eval.eval_client.get_http_client")
    def test_criteria_generation_server_error(self, mock_get_http_client, sample_input_response_examples):
        """Test handling of non-200 server error response."""
        mock_client = MagicMock()
        mock_get_http_client.return_value = mock_client
        error_text = "Internal Server Error"
        mock_client.post.return_value = (error_text, 500)

        with pytest.raises(RuntimeError, match=f"Error input response evaluate: 500 - {error_text}"):
            eval_service_criteria_generation(sample_input_response_examples, api_key="test_key")

    @patch("agent_pilot.eval.eval_client.get_http_client")
    def test_criteria_generation_network_error(self, mock_get_http_client, sample_input_response_examples):
        """Test handling of network errors during the request."""
        mock_client = MagicMock()
        mock_get_http_client.return_value = mock_client
        mock_client.post.side_effect = requests.exceptions.RequestException("Connection failed")

        with pytest.raises(
            RuntimeError, match="Network error while fetching metric generation results: Connection failed"
        ):
            eval_service_criteria_generation(sample_input_response_examples, api_key="test_key")

    @patch("agent_pilot.eval.eval_client.get_http_client")
    def test_criteria_generation_missing_result_in_response(self, mock_get_http_client, sample_input_response_examples):
        """Test handling when 'Result' key is missing in the API response."""
        mock_client = MagicMock()
        mock_get_http_client.return_value = mock_client
        mock_client.post.return_value = ({}, 200)

        with pytest.raises(RuntimeError, match="Metric generation results not found in API response"):
            eval_service_criteria_generation(sample_input_response_examples, api_key="test_key")

    @patch("agent_pilot.eval.eval_client.get_http_client")
    def test_criteria_generation_missing_criteria_in_result(self, mock_get_http_client, sample_input_response_examples):
        """Test handling when 'generated_criteria' is missing in the 'Result' dict."""
        mock_client = MagicMock()
        mock_get_http_client.return_value = mock_client
        api_response_data = {"Result": {"some_other_key": "some_value"}}
        mock_client.post.return_value = (api_response_data, 200)

        with pytest.raises(RuntimeError, match="generated_criteria not found in API response"):
            eval_service_criteria_generation(sample_input_response_examples, api_key="test_key")
