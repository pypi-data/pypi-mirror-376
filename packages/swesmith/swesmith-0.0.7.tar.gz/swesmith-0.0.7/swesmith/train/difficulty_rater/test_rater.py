"""
Purpose: Test the difficulty rater model

Usage: python train/difficulty_rater/test_rater.py --base_url <base_url>

NOTE: Please make sure the sglang server is running and `difficulty_test.jsonl` is in the same directory.
"""

import argparse
import json
import openai

from tqdm.auto import tqdm


def main(base_url: str):
    with open("difficulty_test.jsonl") as f:
        test_insts = [json.loads(x) for x in f]
    client = openai.Client(base_url=f"{base_url}/v1", api_key="swesmith")
    responses = []

    for inst in tqdm(test_insts):
        answer = inst["messages"][-1]["content"]
        messages = inst["messages"][:-1]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            max_tokens=64,
        )
        resp = response.choices[0].message.content.strip()
        pred = resp
        if "\n" in pred:
            pred = pred.split("\n")[0]
        responses.append([pred, answer, resp])

    print(
        f"Accuracy: {round(sum([x[0] == x[1] for x in responses]) / len(responses) * 100, 4)}%"
    )

    sig_diff = 0
    for x in responses:
        if (x[0] == "1-4 hours" and x[1] == "<15 min fix") or (
            x[1] == "1-4 hours" and x[0] == "<15 min fix"
        ):
            sig_diff += 1
    print(f"# of significantly different preds: {sig_diff}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_url", type=str, default="http://localhost:8000")
    args = parser.parse_args()
    main(**vars(args))
