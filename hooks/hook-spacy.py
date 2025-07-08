from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# Collect all spaCy data files and submodules
print('=================== SPACY =====================')
datas = collect_data_files("spacy")
hiddenimports = collect_submodules("spacy")

# If you use spacy_legacy (for older pipelines)
data = collect_all('spacy_legacy')
datas += data[0]
binaries = data[1]
hiddenimports += data[2]

# If you use en_core_web_sm as a package, collect its data too
try:
    data = collect_all('en_core_web_sm')
    datas += data[0]
    binaries += data[1]
    hiddenimports += data[2]
except Exception:
    pass

print('=================== SPACY DONE =====================') 