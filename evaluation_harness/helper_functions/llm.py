from typing import Any
from beartype import beartype

from llms.providers.openai_utils import (
    generate_from_openai_chat_completion,
)

@beartype
def llm_fuzzy_match(pred: str, reference: str, question: str) -> float:
    """
    Check whether the prediction matches the reference with GPT-4-turbo
    """
    messages: list[dict[str, Any]] = []
    # construct the question to ask
    message = "Help a teacher to grade the answer of a student given a question. Keep in mind that the student may use different phrasing or wording to answer the question. The goal is to evaluate whether the answer is semantically equivalent to the reference answer.\n"
    message += f"question: {question}\n"
    message += f"reference answer: {reference}\n"
    message += "all the string 'N/A' that you see is a special sequence that means 'not achievable'\n"
    message += f"student answer: {pred}\n"
    message += "Conclude the judgement by 'correct', 'incorrect', or 'partially correct'. Only output one of these options, and nothing else."
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": message},
    ]

    response = generate_from_openai_chat_completion(
        model="gpt-4-1106-preview",
        messages=messages,
        temperature=0,
        max_tokens=768,
        top_p=1.0,
        context_length=0,
    ).lower()
    print(response)
    if "partially correct" in response or "incorrect" in response:
        return 0.0
    else:
        assert "correct" in response, response
        return 1.0


def llm_ua_match(pred: str, reference: str, question: str) -> float:
    """Check whether the prediction matches the reference with GPT-4-turbo"""
    messages: list[dict[str, Any]] = []
    # construct the question to ask
    message = ""
    message += f"task: {question}\n"
    message += f"actual unachievable reason: {reference}\n"
    message += f"reported unachievable reason: {pred}\n"
    message += (
        "The task described above is inherently unachievable due to the reason specified under 'actual unachievable reason'. "
        "An individual previously attempted this task and was unable to complete it. They provided a reason for their failure, "
        "which is listed under 'reported unachievable reason'. Your role is to review both the actual and reported reasons. "
        "Determine if the reported reason aligns with the actual reason, even if implicitly. "
        "If the stated reason is in line with the actual reason, respond with 'same'. Otherwise, respond with 'different'."
    )
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": message},
    ]

    response = generate_from_openai_chat_completion(
        model="gpt-4-1106-preview",
        messages=messages,
        temperature=0,
        max_tokens=768,
        top_p=1.0,
        context_length=0,
    ).lower()
    if "different" in response:
        return 0.0
    else:
        assert "same" in response
        return 1.0