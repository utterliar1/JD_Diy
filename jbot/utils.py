#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import os
import sys

from jbot import logger


def load_module(module, path):
    files = os.listdir(path)
    for file in files:
        try:
            if file.endswith('.pyc') or file.endswith('.py'):
                filename = file.replace('.pyc', '').replace('.py', '')
                name = "jbot.{}.{}".format(module, filename)
                spec = importlib.util.spec_from_file_location(name, path + file)
                load = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(load)
                sys.modules[f"jbot.{module}.{filename}"] = load
                logger.info(f"Bot加载-->{filename}-->完成")
        except Exception as e:
            logger.info(f"Bot加载失败-->{file}-->{str(e)}")
            continue
