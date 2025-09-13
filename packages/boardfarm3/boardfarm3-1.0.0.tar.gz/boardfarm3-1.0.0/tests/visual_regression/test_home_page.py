"""Visual regression test for prplOS Home Page."""

from typing import Any, Callable

import pytest
from selenium.webdriver.firefox.webdriver import WebDriver

from boardfarm3.lib.gui.prplos.pages.home import HomePage


@pytest.mark.env_req({"environment_def": {"board": {"model": "prplOS"}}})
def test_home_page(
    browser_data_visual_regression: tuple[WebDriver, Any],
    check: Callable,
) -> None:
    """Login Page.

    # noqa: DAR101
    """
    driver, gw_ip = browser_data_visual_regression
    HomePage(driver, gw_ip)
    assert check(  # noqa: S101
        driver,
        "Home page",
        ignore=[
            "div.col-md-3:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(3)",
            "div.col-md-3:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > svg:nth-child(1)",
            "div.col-md-3:nth-child(3) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1)",
            "div.col-md-3:nth-child(3) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > svg:nth-child(1)",
            "div.col-md-3:nth-child(4) > div:nth-child(1) > div:nth-child(1) > svg:nth-child(2)",
            "div.col-md-3:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1)",
        ],
    )
