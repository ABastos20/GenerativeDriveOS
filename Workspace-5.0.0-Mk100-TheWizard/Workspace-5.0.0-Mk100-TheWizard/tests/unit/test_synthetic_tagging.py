from jarvis.simulation.tagging import tag_output, hash_prompt
from jarvis.simulation.origins import OriginType


def test_tag_output_marks_synthetic():
    tag = tag_output("content", generator_id="simulator", model_version="v1", prompt="hello world")
    assert tag.origin == OriginType.SYNTHETIC
    assert tag.generator_id == "simulator"
    assert tag.model_version == "v1"
    assert tag.prompt_hash == hash_prompt("hello world")
