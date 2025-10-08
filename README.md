# 🏃‍➡️ barangay-api
Barangay API - Simple FastAPI wrapper for [barangay](https://pypi.org/project/barangay/)
package.

## 🗺️ Overview

This project is a FastAPI wrapper around the barangay package, providing a simple and
efficient way to interact with the Philippine Standard Geographic Code (PSGC) data.

## 🔦 Features

- Simple and easy to use API.
- Performant barangay fuzzy-search function - can reach **sub-20ms per match**, minus
  network delays. That's roughly 1.1 million match/second!
- FastAPI framework for high performance, auto-documentation, and validation.
- Docker-ready

## 📦 Installation & Usage

### 🐋 Easiest: Using Linux Docker Image
**Use this when:** you have docker and using linux (even WSL):

```
docker run -p 48573:48573 -d bendlikeabamboo/barangay-api
```

Try out the API in your local browser: [`http://localhost:48573/docs`](http://localhost:48573/docs)

### 🐳 Building Docker Image From Source

**Use this when:** you're on other platforms but have docker installed.

To get started, clone the repository.

```bash
git clone https://github.com/bendlikeabamboo/barangay-api
cd barangay-api
```

Build the image
```
docker build --tag 'barangay-api' .
```

Run the image
```
docker run -p 48573:48573 barangay-api
```
Try out the API in your local browser: [`http://localhost:48573/docs`](http://localhost:48573/docs)


### 🐍 Using Python From Source

**Use this when:** you don't have docker but have Python >3.12 installed or would like
to develop & contribute.

To get started, clone the repository.

```bash
git clone https://github.com/bendlikeabamboo/barangay-api
cd barangay-api
```
Then install the package:

```
pip install .
```

Once successful, run using uvicorn:

```bash
uvicorn barangay_api.main:app --port 48573
```

Try out the API in your local browser: [`http://localhost:48573/docs`](http://localhost:48573/docs)

## License

This project is licensed under the MIT License. See the LICENSE file for more details.