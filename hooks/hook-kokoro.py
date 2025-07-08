from PyInstaller.utils.hooks import collect_data_files
import os

# Path to the downloaded Kokoro model in the Hugging Face cache
model_path = os.path.expanduser('~/.cache/huggingface/hub/models--hexgrad--Kokoro-82M')

if os.path.exists(model_path):
    print(f"Including Kokoro model from: {model_path}")
    datas = collect_data_files(model_path, subdir='models--hexgrad--Kokoro-82M')
else:
    print(f"Kokoro model not found at: {model_path}")
    datas = []

# Also include misaki/data directory for required JSON files
misaki_data_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'kokoro-env', 'lib', 'python3.11', 'site-packages', 'misaki', 'data'))
if os.path.exists(misaki_data_path):
    print(f"Including misaki data from: {misaki_data_path}")
    datas += collect_data_files(misaki_data_path, subdir='misaki/data')
else:
    print(f"misaki data not found at: {misaki_data_path}") 