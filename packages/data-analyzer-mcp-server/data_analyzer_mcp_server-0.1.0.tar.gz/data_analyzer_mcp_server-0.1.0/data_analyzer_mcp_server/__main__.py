# !/user/bin/env python
# coding: utf-8
"""
@Time       : 2025/9/14 18:02
@Auther     : clip@gmail.com
@File       : __main__.py.py
"""
from .core import serve


if __name__ == "__main__":
    import asyncio
    asyncio.run(serve())