#!/bin/bash

# MinerU API 服务启动脚本 v2.0
# 指定在4060Ti上运行
CUDA_VISIBLE_DEVICES=1 python api_server.py