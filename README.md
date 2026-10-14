# Waste App Backend

## Overview

The backend powers the waste detection workflow by identifying waste items from an uploaded image, retrieving disposal instructions, and suggesting nearby recycling centers.

## Workflow

```text
User uploads an image
        │
        ▼
FastAPI receives the image
        │
        ▼
Vision AI analyzes the image
        │
        ▼
Returns:
- Waste type (Recyclable / Non-Recyclable)
- Material
        │
        ▼
Check Redis Cache
        │
        ├── Cache Hit
        │       │
        │       ▼
        │  Return disposal instructions
        │
        └── Cache Miss
                │
                ▼
        Query PostgreSQL
                │
                ▼
        Cache the result in Redis
                │
                ▼
Find nearby recycling centers
        │
        ▼
Return complete response to the client
        │                       |
        ▼                       ▼
Search PostgreSQL       User submits a recycling center
(Verified Centers)
            │
     ┌──────┴──────┐
     │             │
 Found        Not Found
     │             │
     ▼             ▼
Return        Search Google Places
Verified            │
Centers             ▼
               Return Results
```

## Features

- Image-based waste detection using a model
- Material classification
- Disposal instructions lookup
- Redis caching for faster lookups
- Rate limiting on image upload API
- Nearby recycling center discovery