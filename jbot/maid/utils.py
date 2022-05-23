#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio


async def executes(command, pass_error=True):
    """ 执行命令并返回输出，并选择启用stderr. """
    executor = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await executor.communicate()
    except Exception as e:
        return f"加载出错--->{str(e)}"
    if pass_error:
        result = str(stdout.decode().strip()) + str(stderr.decode().strip())
    else:
        result = str(stdout.decode().strip())
    return result
