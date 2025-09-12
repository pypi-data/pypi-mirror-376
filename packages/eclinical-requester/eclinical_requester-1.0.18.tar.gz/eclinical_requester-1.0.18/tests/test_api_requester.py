# !/usr/bin/python3
# -*- coding:utf-8 -*-
"""
@Author: xiaodong.li
@Time: 5/15/2025 3:11 PM
@Description: Description
@File: test_api_requester.py
"""
import json
import unittest

from api_requester.core.call_api import ApiRequester
from api_requester.utils.constant import AppEnum, EdcAppType
from api_requester.utils.decrypt import decrypt


class TestApiRequester(unittest.TestCase):
    @staticmethod
    def test_app_login():
        c = ApiRequester("auto_api_coding", "Admin@123", "For CODING automated testing", "Study", "dev03", "dev",
                         app=AppEnum.CODING.code, company="For internal automated testing", role="DM")
        c.login()

    @staticmethod
    def test_procheck_login():
        c = ApiRequester("CRC01", "Admin@123", "Edetek", None, "dev03", "dev",
                         app=AppEnum.PROCHECK.code, company="Edetek", role="DM")
        c.login()

    @staticmethod
    def test_cmd_login():
        c = ApiRequester("CRC01", "Admin@123", None, None, "dev03", None,
                         app=AppEnum.CMD.code, company="Edetek", company_level_login=True)
        c.login()

    @staticmethod
    def test_ecoa_login():
        c = ApiRequester("CRC01", "7IG4CALi", app=AppEnum.EDC.code, test_env="dev03", ttype=EdcAppType.ECOA.name)
        c.login()
        assert c.user.study == 'Study-229-2436'
        response = c.request("get", "/mobile/user/ecoa-study-language")
        assert response.json().get("payload")

    @staticmethod
    def test_ediary_login():
        c = ApiRequester("31176557", "886506", app=AppEnum.EDC.code, test_env="dev03", ttype=EdcAppType.EDIARY.name)
        c.login()
        response = c.request("get", "/study/information")
        assert response.json().get("payload").get("name") == 'Study-229-2436'

    @staticmethod
    def test_ediary_login_with_org_code():
        c = ApiRequester("76548847", "340196", app=AppEnum.EDC.code, test_env="dev01", ttype=EdcAppType.EDIARY.name,
                         org_code="62B64A")
        c.login()
        response = c.request("get", "/study/information")
        assert response.json().get("payload").get("name") == "Study-113-963"

    @staticmethod
    def test_ediary_login_with_no_org_code():
        c = ApiRequester("76548847", "340196", app=AppEnum.EDC.code, test_env="dev01", ttype=EdcAppType.EDIARY.name,
                         org_code="")
        c.login()
        response = c.request("get", "/study/information")
        assert response.json().get("payload").get("name") == "Study-113-963"

    @staticmethod
    def test_ediary_data_with_org_code():
        c = ApiRequester("76548847", "340196", app=AppEnum.EDC.code, test_env="dev01", ttype=EdcAppType.EDIARY.name,
                         org_code="62B64A")
        c.login()
        response = c.request("post", "/e-diary-app/offline/subject-version")
        payload = response.json().get("payload")
        node = decrypt(payload, is_no_padding=True)
        print(json.loads(node))

    @staticmethod
    def test_get_by_token():
        c = ApiRequester(app=AppEnum.DESIGN.code, test_env="dev03",
                         token="DESIGN eyJhbGciOiJIUzUxMiJ9.eyJ1aWQiOiI4MzM4OTYxZjgzMzc0OWU3YTQwMzcxYWU2MjNjYjk0ZCIsInN1YiI6IlVzZXJ8fENSQzAxfHwxfHwwIiwid2lkIjoiNDdkNmY0NzI3ZTgzNDRmOWJkYjNjOWZiNDc5MmMwYWEiLCJjcmVhdGVkIjoxNzUzNDI5MjIxOTk0LCJleHAiOjE3NjEyMDUyMjF9.GmTtnjobE8RByKBjrRfj8nxjXNgevpmcHRPCRkFD7OEjcdZSW69fX3VBSlSgSXtHAQrdaEPr5W0n6EefNngKWQ")
        c.login()
        response = c.request("GET", "/study")
        payload = response.json().get("payload")
        print(payload)
