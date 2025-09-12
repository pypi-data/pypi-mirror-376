# -*- coding: utf-8 -*-
# Name of current package.
# Import built-in modules

PACKAGE_NAME = "arthub_login_widgets"
ARTHUB_RESET_PASSWORD_WEB_URL = "https://arthub.qq.com/reset-password"
ARTHUB_SET_ACCOUNT_INFO_WEB_URL = "https://arthub.qq.com/regist/personal?accountName="
UI_TEXT_MAP = {
    "window_title": ["Log in to ArtHub", "登录 ArtHub"],
    "account_placeholder": ["Email/Phone", "邮箱/手机号"],
    "password_placeholder": ["Password", "密码"],
    "login_button": ["Log in", "登录"],
    "forgot_password_button": ["Forgot password", "忘记密码"],
}

SERVICE_CONFIGS = {
    "test": {
        "api": "service.arthubcn-test.qq.com",
        "page": "arthubcn-test.qq.com"
    },
    "mainland": {
        "api": "service.arthubcn.qq.com",
        "page": "arthubcn.qq.com"
    },
    "overseas": {
        "api": "service.arthubint.qq.com",
        "page": "arthubint.qq.com"
    }
}

ARTHUB_TEST_QQ_COM_SERVICE_ID = 11000
ARTHUB_TEST2_QQ_COM_SERVICE_ID = 11001
ARTHUB_QQ_COM_SERVICE_ID = 11000
ARTHUBDAM_COM_SERVICE_ID = 11001
ARTHUBSG_QQ_COM_SERVICE_ID = 11000
