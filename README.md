# Nearby Dustbin Finder - Backend

## Overview

The backend powers a crowdsourced waste-disposal and sanitation platform that helps users discover nearby dustbins, verify their locations, report their conditions, and help authorities prioritize waste collection.

Built with **FastAPI and PostgreSQL**, the platform combines geospatial discovery, community-generated data, confidence-based verification, and waste classification to improve access to disposal points and the reliability of waste-management information.

## Core Workflows

### 1. Dustbin Discovery

Users can discover nearby dustbins using their current location.

```text
User shares location
        |
        v
FastAPI receives coordinates
        |
        v
Find nearby dustbins in PostgreSQL
        |
        v
Calculate distance and rank results
        |
        v
Return nearby dustbins
        |
        v
User selects a dustbin
        |
        v
Navigate using Google Maps
```

Each dustbin can include its location, user-assigned name, photos, public accessibility, accepted waste types, confidence score, and last verification time.

### 2. Community-Powered Dustbin Discovery

Users can contribute new dustbins that are missing from the platform.

```text
User submits a dustbin
        |
        v
Upload photos and location
        |
        v
FastAPI validates the submission
        |
        v
Store image metadata and dustbin details
        |
        v
Initialize confidence score
        |
        v
Dustbin becomes discoverable
        |
        v
Other users verify its existence
        |
        v
Update confidence based on feedback
```

Photo evidence helps improve the quality of community-submitted data. Independent user feedback helps identify reliable locations and potentially missing or removed dustbins.

### 3. Dustbin Verification and Condition Reporting

Users can report whether a dustbin still exists and provide observations about its condition.

```text
User reaches a dustbin
        |
        v
Submit feedback
        |
        +---------------------+
        |                     |
        v                     v
   Exists: Yes           Exists: No
        |                     |
        v                     v
Increase confidence     Decrease confidence
        |                     |
        +----------+----------+
                   |
                   v
          Aggregate feedback
                   |
                   v
       Update dustbin reliability
```

Condition reports can also capture fill levels and cleanliness. Aggregated observations help identify dustbins that may require attention.

### 4. Sanitation and Collection Prioritization

Condition reports can help authorities identify dustbins that need collection or cleaning.

```text
User condition reports
        |
        v
Aggregate recent observations
        |
        v
Evaluate fill level, cleanliness,
report frequency and recency
        |
        v
Calculate collection priority
        |
        v
Identify high-priority dustbins
        |
        v
Authority dashboard
```

The priority score can combine reported fill levels, time since collection, report frequency, and data reliability. This provides a foundation for future collection scheduling and route optimization.


## Technology Stack

- **Backend:** FastAPI, Python
- **Database:** PostgreSQL
- **Caching:** Redis
- **AI:** Vision language model for waste identification
- **Image storage:** Amazon S3
- **Geospatial search:** Coordinate-based distance calculations, with PostGIS as a potential extension

## Project Goals

- Make waste-disposal points easier to discover in unfamiliar areas.
- Improve the accuracy of crowdsourced dustbin locations through community verification.
- Identify overflowing or poorly maintained dustbins using aggregated reports.
- Help sanitation authorities prioritize collection and cleaning operations.
- Provide accessible disposal guidance for waste that requires special handling.

