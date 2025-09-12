# ToolBoxAI-Dashboard

![Build Status](https://github.com/grayghostdev/ToolBoxAI-Dashboard/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Coverage](https://img.shields.io/badge/coverage-unknown-lightgrey)

A modern, enterprise-grade dashboard for the Roblox Educational Training Platform.

## Getting Started

1. Clone the repository:
   ```sh
   git clone https://github.com/grayghostdev/ToolBoxAI-Dashboard.git
   cd ToolBoxAI-Dashboard
   ```
2. Install dependencies:
   ```sh
   npm install
   # or for Python backend
   pip install -r requirements.txt
   ```
3. Start the development server:
   ```sh
   npm run dev
   # or for FastAPI backend
   uvicorn backend.api.education:router --reload
   ```

## Project Structure

- Frontend: React 18 + TypeScript + Material-UI + Redux Toolkit
- Backend: FastAPI, integrated with Ghost backend

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

MIT
