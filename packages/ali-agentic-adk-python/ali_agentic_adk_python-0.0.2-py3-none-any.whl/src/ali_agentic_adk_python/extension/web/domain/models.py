# Copyright (C) 2025 AIDC-AI
# This project incorporates components from the Open Source Software below.
# The original copyright notices and the licenses under which we received such components are set forth below for informational purposes.
#
# Open Source Software Licensed under the MIT License:
# --------------------------------------------------------------------
# 1. vscode-extension-updater-gitlab 3.0.1 https://www.npmjs.com/package/vscode-extension-updater-gitlab
# Copyright (c) Microsoft Corporation. All rights reserved.
# Copyright (c) 2015 David Owens II
# Copyright (c) Microsoft Corporation.
# Terms of the MIT:
# --------------------------------------------------------------------
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from typing import Optional

class BrowserUseRequest():
    """浏览器使用请求"""
    command: str
    region_id: Optional[str] = None
    endpoint: Optional[str] = None
    computer_resource_id: Optional[str] = None
    timeout: Optional[int] = 30


class BrowserUseResponse():
    """浏览器使用响应"""
    is_success: bool
    message: str
    browser_use_output: Optional[str] = None
    dropped: Optional[int] = None

    def __init__(self, is_success: bool, message: str, browser_use_output: Optional[str] = None, dropped: Optional[int] = None, **data):
        super().__init__(
            is_success=is_success,
            message=message,
            browser_use_output=browser_use_output,
            dropped=dropped,
            **data
        )
    
    @classmethod
    def success(cls, message: str = "操作成功", browser_use_output: Optional[str] = None) -> "BrowserUseResponse":
        """创建成功响应"""
        return cls(is_success=True, message=message, browser_use_output=browser_use_output)
    
    @classmethod
    def error(cls, message: str = "操作失败", dropped: Optional[int] = None) -> "BrowserUseResponse":
        """创建错误响应"""
        return cls(is_success=False, message=message, dropped=dropped)
