# !/user/bin/env python
# coding: utf-8
"""
@Time       : 2025/9/14 18:02
@Auther     : clip@gmail.com
@File       : cli.py
"""
from .core import serve


def main():
    import asyncio
    asyncio.run(serve())