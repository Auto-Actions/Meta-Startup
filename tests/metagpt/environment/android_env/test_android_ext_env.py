#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of AndroidExtEnv


from metagpt.const import ADB_EXEC_FAIL
from metagpt.environment.android_env.android_ext_env import AndroidExtEnv


def mock_device_shape(self, adb_cmd: str) -> str:
    return "shape: 720x1080"


def mock_device_shape_invalid(self, adb_cmd: str) -> str:
    return ADB_EXEC_FAIL


def mock_list_devices(self, adb_cmd: str) -> str:
    return "devices\nemulator-5554"


def mock_get_screenshot(self, adb_cmd: str) -> str:
    return "screenshot_xxxx-xx-xx"


def mock_get_xml(self, adb_cmd: str) -> str:
    return "xml_xxxx-xx-xx"


def mock_write_read_operation(self, adb_cmd: str) -> str:
    return "OK"


def test_android_ext_env(mocker):
    device_id = "emulator-5554"
    mocker.patch(
        "metagpt.environment.android_env.android_ext_env.AndroidExtEnv.execute_adb_with_cmd", mock_device_shape
    )

    ext_env = AndroidExtEnv(device_id=device_id, screenshot_dir="/data2/", xml_dir="/data2/")
    assert ext_env.adb_prefix == f"adb -s {device_id} "
    assert ext_env.adb_prefix_shell == f"adb -s {device_id} shell "
    assert ext_env.adb_prefix_si == f"adb -s {device_id} shell input "

    assert ext_env.device_shape == (720, 1080)

    mocker.patch(
        "metagpt.environment.android_env.android_ext_env.AndroidExtEnv.execute_adb_with_cmd", mock_device_shape_invalid
    )
    assert ext_env.device_shape == (0, 0)

    mocker.patch(
        "metagpt.environment.android_env.android_ext_env.AndroidExtEnv.execute_adb_with_cmd", mock_list_devices
    )
    assert ext_env.list_devices() == [device_id]

    mocker.patch(
        "metagpt.environment.android_env.android_ext_env.AndroidExtEnv.execute_adb_with_cmd", mock_get_screenshot
    )
    assert ext_env.get_screenshot("screenshot_xxxx-xx-xx", "/data/") == "/data/screenshot_xxxx-xx-xx.png"

    mocker.patch("metagpt.environment.android_env.android_ext_env.AndroidExtEnv.execute_adb_with_cmd", mock_get_xml)
    assert ext_env.get_xml("xml_xxxx-xx-xx", "/data/") == "/data/xml_xxxx-xx-xx.xml"

    mocker.patch(
        "metagpt.environment.android_env.android_ext_env.AndroidExtEnv.execute_adb_with_cmd", mock_write_read_operation
    )
    res = "OK"
    assert ext_env.system_back() == res
    assert ext_env.system_tap(10, 10) == res
    assert ext_env.user_input("test_input") == res
    assert ext_env.user_longpress(10, 10) == res
    assert ext_env.user_swipe(10, 10) == res
    assert ext_env.user_swipe_to((10, 10), (20, 20)) == res
