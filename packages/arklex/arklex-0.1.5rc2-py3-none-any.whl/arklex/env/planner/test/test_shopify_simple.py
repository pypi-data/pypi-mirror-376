# Install required packages in the root directory: pip install -e .
# Go to the parent folder of this file (shopify), then Run python -m unittest test.py to test the code in this file.

import json
import os
import time
import unittest
import warnings
from typing import Any

from arklex.env.env import Environment
from arklex.orchestrator.orchestrator import AgentOrg

# Wait this many seconds between tests to avoid token rate-limiting
WAIT_TIME_BETWEEN_TESTS_SEC: int | None = 5  # Set to None or 0 for no wait time


class Logic_Test(unittest.TestCase):
    file_path: str = "test_cases_shopify_simple.json"
    with open(file_path, encoding="UTF-8") as f:
        TEST_CASES: list[dict[str, Any]] = json.load(f)

    @classmethod
    def setUpClass(cls) -> None:
        """Method to prepare the test fixture. Run BEFORE the test methods."""
        cls.user_prefix: str = "user"
        cls.worker_prefix: str = "assistant"
        cls.config: dict[str, Any] | None = None
        cls.env: Environment | None = None
        cls.total_tests_run: int = 0

    @classmethod
    def tearDownClass(cls) -> None:
        """Method to tear down the test fixture. Run AFTER the test methods."""

    def _get_api_bot_response(
        self, user_text: str, history: list[dict[str, str]], params: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        data: dict[str, Any] = {
            "text": user_text,
            "chat_history": history,
            "parameters": params,
        }
        orchestrator: AgentOrg = AgentOrg(config=self.config, env=self.env)
        result: dict[str, Any] = orchestrator.get_response(data)

        return result["answer"], result["parameters"]

    def _check_task_completion(
        self, output: str, params: dict[str, Any], test_case: dict[str, Any]
    ) -> None:
        expected_output: dict[str, Any] = test_case.get("expected_output", {})
        contains: dict[str, list[str]] = expected_output.get("contains", {})
        contains_all: list[str] = contains.get("all", [])
        contains_any: list[str] = contains.get("any", [])

        if len(contains_all) > 0:
            for text in contains_all:
                failure_message: str = f"FAILED: Expected text '{text}' not found in final output ('{output}'). params['memory']['function_calling_trajectory'] = {params['memory']['function_calling_trajectory']}"
                self.assertTrue(text.lower() in output.lower(), failure_message)

        if len(contains_any) > 0:
            contains_flags: list[bool] = [
                text.lower() in output.lower() for text in contains_any
            ]
            failure_message: str = f"FAILED: None of {contains_any} were found in final output ('{output}'). params['memory']['function_calling_trajectory'] = {params['memory']['function_calling_trajectory']}"
            self.assertTrue(True in contains_flags, failure_message)

    def _check_tool_calls(
        self, params: dict[str, Any], env: Environment, test_case: dict[str, Any]
    ) -> None:
        _expected_tool_calls: dict[str, Any] = test_case.get("expected_tool_calls", {})

        # Check if multiple possible tool call sequences are allowed to pass this test
        # (E.g., get_products or get_web_product)
        _allowed_tool_calls: list[dict[str, Any]] | None = _expected_tool_calls.get(
            "options"
        )
        if _allowed_tool_calls is None:
            _allowed_tool_calls = [_expected_tool_calls]

        # Reformat tool/worker names to match those found in conversation history (which
        # are not necessarily the same names as those found in taskgraph.json)
        expected_tool_calls: list[dict[str, Any]] = []
        for tool_set in _allowed_tool_calls:
            expected_tool_set: dict[str, Any] = {}
            for tool_name in tool_set:
                for resource_name in env.planner.all_resources_info:
                    if tool_name in resource_name:
                        expected_tool_set[resource_name] = tool_set[tool_name]
                        break
            expected_tool_calls.append(expected_tool_set)

        # Get actual tool calls from conversation history
        actual_tool_calls: dict[str, int] = {}
        for msg in params["memory"]["function_calling_trajectory"]:
            if msg["role"] == "tool":
                tool_name: str = msg["name"]

                if tool_name in actual_tool_calls:
                    actual_tool_calls[tool_name] += 1
                else:
                    actual_tool_calls[tool_name] = 1

        # If only one set of tool calls is allowed to pass this test, check that actual tool
        # calls match these exactly
        if len(expected_tool_calls) == 1:
            expected_tool_calls: dict[str, Any] = expected_tool_calls[0]
            failure_message: str = (
                "FAILED: Planner expected tool calls != actual tool calls."
                + f"\nexpected_tool_calls = {json.dumps(expected_tool_calls, indent=2)}"
                + f"\nactual_tool_calls = {json.dumps(actual_tool_calls, indent=2)}"
                + f"\nparams['memory']['function_calling_trajectory'] = {params['memory']['function_calling_trajectory']}"
            )
            self.assertEqual(expected_tool_calls, actual_tool_calls, failure_message)

        # If multiple possible tool call sequences are allowed, check that actual tool calls
        # matches at least one of these
        else:
            failure_message: str = (
                "FAILED: Planner allowed tool calls != actual tool calls."
                + "\nActual tool calls was expected to be one of the following:"
            )
            for tool_set in expected_tool_calls:
                failure_message += f"\n{json.dumps(tool_set, indent=2)}"
            failure_message += (
                f"\nInstead, actual_tool_calls were: {json.dumps(actual_tool_calls, indent=2)}"
                + f"\nparams['memory']['function_calling_trajectory'] = {params['memory']['function_calling_trajectory']}"
            )

            tool_call_matches: list[bool] = [
                actual_tool_calls == tool_set for tool_set in expected_tool_calls
            ]
            self.assertTrue(True in tool_call_matches, failure_message)

    def _check_success_criteria(
        self, output: str, params: dict[str, Any], test_case: dict[str, Any]
    ) -> None:
        self._check_tool_calls(params, self.env, test_case)
        self._check_task_completion(output, params, test_case)

    def _run_test_case(self, idx: int) -> None:
        # Wait to avoid token rate-limiting
        if WAIT_TIME_BETWEEN_TESTS_SEC is not None and self.total_tests_run > 0:
            print(
                f"\nWaiting {WAIT_TIME_BETWEEN_TESTS_SEC} sec between tests to avoid token rate-limiting..."
            )
            time.sleep(WAIT_TIME_BETWEEN_TESTS_SEC)

        print(f"\n=============Unit Test {idx}=============")

        test_case: dict[str, Any] = self.TEST_CASES[idx]
        print(f"Task description: {test_case['description']}")

        # Initialize config and env
        file_path: str = test_case["taskgraph"]
        input_dir: str
        _: str
        input_dir, _ = os.path.split(file_path)
        with open(file_path, encoding="UTF_8") as f:
            self.config = json.load(f)
        self.env = Environment(
            tools=self.config.get("tools", []),
            workers=self.config.get("workers", []),
            agents=self.config.get("agents", []),
            slotsfillapi=self.config["slotfillapi"],
            planner_enabled=True,
        )

        history: list[dict[str, str]] = []
        params: dict[str, Any] = {}
        for node in self.config["nodes"]:
            if node[1].get("type", "") == "start":
                start_message: str = node[1]["attribute"]["value"]
                break
        history.append({"role": self.worker_prefix, "content": start_message})

        for user_text in test_case["user_utterance"]:
            print(f"User: {user_text}")
            output: str
            params: dict[str, Any]
            output, params = self._get_api_bot_response(user_text, history, params)
            print(f"Bot: {output}")
            history.append({"role": self.user_prefix, "content": user_text})
            history.append({"role": self.worker_prefix, "content": output})

        print(f"Success criteria: {test_case['criteria']}")
        final_output: str = history[-1]["content"]
        self._check_success_criteria(final_output, params, test_case)

        self.total_tests_run += 1

    def test_Unittest00(self) -> None:
        self._run_test_case(0)

    def test_Unittest01(self) -> None:
        self._run_test_case(1)

    def test_Unittest02(self) -> None:
        self._run_test_case(2)

    def test_Unittest03(self) -> None:
        self._run_test_case(3)

    def test_Unittest04(self) -> None:
        self._run_test_case(4)

    def test_Unittest05(self) -> None:
        self._run_test_case(5)

    def test_Unittest06(self) -> None:
        self._run_test_case(6)

    def test_Unittest07(self) -> None:
        self._run_test_case(7)

        # Since this test updates a cart, ensure that the cart's contents have actually been updated
        cart_id: str = "gid://shopify/Cart/Z2NwLXVzLWVhc3QxOjAxSlFTNDgxVlFBOE4yN1g1UkpHNkIyUEVH?key=f21355e2f1f6491ddc8a6d667ad1104f"
        kwargs: dict[str, str] = {"cart_id": cart_id}
        resource_id: int = self.env.planner.name2id["shopify-get_cart-get_cart"]
        calling_tool: dict[str, Any] = self.env.planner.tools_map[resource_id]
        combined_kwargs: dict[str, Any] = {**kwargs, **calling_tool["fixed_args"]}
        observation: str = str(calling_tool["execute"]().func(**combined_kwargs))

        # Check for information related to the added product
        self.assertTrue("gid://shopify/Product/8970008461542" in observation)
        self.assertTrue("Inyahome New Art Velvet" in observation)
        self.assertTrue("Pillow Cove" in observation)

    def test_Unittest08(self) -> None:
        self._run_test_case(8)

    def test_Unittest09(self) -> None:
        self._run_test_case(9)


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        unittest.main()
