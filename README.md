# barangay-api
Barangay API - Simple FastAPI wrapper for [barangay](https://pypi.org/project/barangay/)
package.

## Overview

This project is a FastAPI wrapper around the barangay package, providing a simple and
efficient way to interact with the Philippine Standard Geographic Code (PSGC) data.

## Features

- Simple and easy to use API.
- FastAPI framework for high performance.
- Docker-ready

## Usage

## Installation & Usage
To get started, clone the repository.

```bash
git clone https://github.com/bendlikeabamboo/barangay-api
cd barangay-api
```
From here, you can install & run the application using two methods.
### Using Python
```
pip install .
```
Once successful, run using uvicorn:
```bash
uvicorn barangay_api.main:app --port 48573
```

Try out the API in your local browser: `http://localhost:48573`

### Using Docker
Build the image
```
docker build --tag 'barangay-api' .
```

Run the image
```
docker run -p 48573:48573 barangay-api
```
Try out the API in your local browser: `http://localhost:48573`

## License

This project is licensed under the MIT License. See the LICENSE file for more details.