conda init --all
bash
sudo apt-get update
sudo apt-get install ffmpeg -y
sudo apt-get install mesa-va-drivers -y
conda create --name facefusion python=3.12 -y
conda activate facefusion
python install.py --onnxruntime default
conda install conda-forge::cuda-runtime=12.4.1 conda-forge::cudnn=9.2.1.18 -y
pip install tensorrt==10.6.0 --extra-index-url https://pypi.nvidia.com
conda deactivate
conda activate facefusion