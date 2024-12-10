conda init --all
bash
sudo apt-get update
sudo apt-get install ffmpeg -y
apt-get install mesa-va-drivers -y
conda create --name facefusion python=3.12 -y
conda activate facefusion
python install.py --onnxruntime default
conda deactivate
conda activate facefusion