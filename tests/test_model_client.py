from tracelens.runtime.model_client import MockModelClient


def test_mock_client_is_deterministic():
    client = MockModelClient()

    first = client.complete("What is the deductible?")
    second = client.complete("What is the deductible?")

    assert first == second


def test_mock_client_scales_tokens_with_prompt_length():
    client = MockModelClient()

    short = client.complete("hi")
    long = client.complete("a " * 200)

    assert long.tokens_in > short.tokens_in
    assert long.cost > short.cost
    assert long.latency_ms > short.latency_ms


def test_mock_client_never_returns_zero_tokens():
    client = MockModelClient()

    response = client.complete("")

    assert response.tokens_in >= 1
    assert response.tokens_out >= 1
