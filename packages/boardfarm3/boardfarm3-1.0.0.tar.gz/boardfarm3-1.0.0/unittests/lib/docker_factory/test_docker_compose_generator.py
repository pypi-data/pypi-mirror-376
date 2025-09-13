"""Unit tests for docker-compose generator module."""

from __future__ import annotations

from json import loads
from pathlib import Path

import pytest

from boardfarm3.lib.boardfarm_config import get_json, parse_boardfarm_config
from boardfarm3.lib.docker_factory.docker_compose_generator import (
    DockerComposeGenerator,
)

_TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture(name="template_manager")
def fixture_template_manager() -> DockerComposeGenerator:
    ams_path = _TEST_DATA_DIR / "ams.json"
    environment_json_path = _TEST_DATA_DIR / "test_environment.json"
    inventory_json = loads(ams_path.read_text())
    boardfarm_config = parse_boardfarm_config(
        inventory_json["F5685LGE-1-1"],
        get_json(environment_json_path.as_posix()),
    )
    return DockerComposeGenerator(boardfarm_config)


def test_docker_compose_generator(template_manager: DockerComposeGenerator) -> None:
    expected_compose_path = _TEST_DATA_DIR / "expected_compose.json"
    expected_compose = loads(expected_compose_path.read_text())
    assert dict(sorted(template_manager.generate_docker_compose().items())) == dict(
        sorted(expected_compose.items()),
    )


@pytest.mark.parametrize(
    (
        "data",
        "val_from",
        "val_to",
        "expected",
    ),
    [
        ([1, 2, 3], 2, "a", [1, "a", 3]),
        ({"a": 1, "b": 2}, 2, "x", {"a": 1, "b": "x"}),
    ],
)
def test_replace_basic(
    template_manager: DockerComposeGenerator,
    data: list[int],
    val_from: int,
    val_to: str,
    expected: list[int | str],
) -> None:
    actual = template_manager._replace(data, val_from, val_to)
    assert actual == expected


@pytest.mark.parametrize(
    ("data", "val_from", "val_to"),
    [([[1, 2], [3, 4]], 2, "a"), ({"a": {"b": 2}}, 2, "x")],
)
def test_replace_nested(
    template_manager: DockerComposeGenerator,
    data: list[list[int]] | dict[str, int],
    val_from: int,
    val_to: str,
) -> None:
    actual = template_manager._replace(data, val_from, val_to)
    expected = template_manager._replace(data, val_from, val_to)
    assert actual == expected


def test_replace_no_match(template_manager: DockerComposeGenerator) -> None:
    data = [1, 2, 3]
    val_from = 4
    val_to = "x"
    actual = template_manager._replace(data, val_from, val_to)
    assert actual == data
