[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sentinelmft"  # <-- change if your package has a different name
version = "0.1.2"     # bump on every upload
description = "AI-powered secure managed file transfer (GCS + AES-256-GCM + anomaly detection)"
readme = { file = "README.md", content-type = "text/markdown" }
requires-python = ">=3.9"
license = { text = "MIT" }
authors = [{ name = "Raghava Chellu" }]
keywords = ["mft","gcp","gcs","encryption","aes-gcm","anomaly-detection","devsecops"]
classifiers = [
  "Programming Language :: Python :: 3",
  "License :: OSI Approved :: MIT License",
  "Operating System :: OS Independent",
  "Topic :: Security :: Cryptography",
  "Topic :: System :: Networking",
  "Intended Audience :: Developers"
]

[project.urls]
Homepage = "https://github.com/RaghavaCh440/sentinelmft"
Documentation = "https://github.com/RaghavaCh440/sentinelmft#readme"
Source = "https://github.com/RaghavaCh440/sentinelmft"
Issues = "https://github.com/RaghavaCh440/sentinelmft/issues"

[tool.setuptools]
packages = { find = { where = ["src"] } }

[tool.setuptools.packages.find]
where = ["src"]

[project.scripts]
sentinelmft = "sentinelmft.cli:app"

