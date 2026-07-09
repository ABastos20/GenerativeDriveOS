import threading
import time

class LLMGlobalBudgetGuard:
    """
    HARD GLOBAL TOKEN BUDGET ACROSS ENTIRE RUNTIME
    Thread-safe implementation to prevent runaway costs.
    """

    def __init__(self, max_usd: float, cost_per_1k_tokens: float):
        self.max_usd = max_usd
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.spent_usd = 0.0
        self.lock = threading.Lock()

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000.0) * self.cost_per_1k_tokens

    def assert_can_spend(self, prompt: str, max_output_tokens: int):
        est_input_tokens = len(prompt) / 4  # conservative heuristic
        est_cost = self.estimate_cost(est_input_tokens, max_output_tokens)

        with self.lock:
            if self.spent_usd + est_cost > self.max_usd:
                raise RuntimeError(
                    f"🚨 LLM BUDGET EXCEEDED: "
                    f"Spent=${self.spent_usd:.2f}, "
                    f"Attempted=${est_cost:.2f}, "
                    f"Limit=${self.max_usd}"
                )

    def register_spend(self, usage):
        """
        Usage object expected to have input_tokens and output_tokens (or similar).
        Adapts to Gemini usage object.
        """
        # Gemini usage object usually has prompt_token_count and candidates_token_count
        input_t = getattr(usage, "prompt_token_count", 0)
        output_t = getattr(usage, "candidates_token_count", 0)
        
        # Fallback if standard attribs
        if input_t == 0 and hasattr(usage, "input_tokens"):
             input_t = usage.input_tokens
        if output_t == 0 and hasattr(usage, "output_tokens"):
             output_t = usage.output_tokens
             
        with self.lock:
            actual_cost = self.estimate_cost(input_t, output_t)
            self.spent_usd += actual_cost

            print(
                f"[BUDGET] +${actual_cost:.4f} | "
                f"Total=${self.spent_usd:.2f}/${self.max_usd}"
            )
