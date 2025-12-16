#!/bin/bash
echo 启动中，根据机器情况需要等待30几秒…… 
eval "$(conda shell.bash hook)"
source activate facefusion
cd /root/facefusion
python facefusion.py run