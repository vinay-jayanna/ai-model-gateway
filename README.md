# VPS Model Gateway

## Overview

This project is a FastAPI application designed to act as a gateway to ML models deployed across various Kubernetes clusters. It includes user authentication, authorization, caching, and data pre/post-processing capabilities.

## Development

To run the application locally:

```bash
uvicorn app.main:app --reload
