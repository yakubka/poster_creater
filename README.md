# Auto Poster Generator

Auto Poster Generator is a fully functional Python script that
automatically parses car data from https://www.automobile-catalog.com
and generates a poster in the style of the provided reference (e.g.,
"AUDI TT RS").

The script:

-   accepts a car name (e.g., `Audi TT RS`)
-   automatically finds the corresponding model on the website
-   parses technical specifications
-   fetches a car image (via Unsplash API)
-   removes the background (via remove.bg API)
-   generates a styled poster
-   saves the result as a PNG image

The main priority of this project is the final visual output matching
the reference style.

------------------------------------------------------------------------

## How It Works

### 1. Data Search and Parsing

The script uses Selenium (undetected_chromedriver) to interact with
automobile-catalog.com.

Process:

1.  Opens the brand page (e.g., `list-audi.html`)
2.  Automatically finds the requested model
3.  Navigates to the specifications page
4.  Parses:
    -   Engine
    -   Power
    -   Torque
    -   0--100 km/h
    -   Top speed
    -   Weight
    -   Year

### Cloudflare and "I am human" Verification

The website is protected by Cloudflare.

On the first run:

-   A browser window will open.
-   You must manually complete the "I am human" verification.
-   After successful verification, the script saves cookies to
    `cookies_selenium.pkl`.

After that:

-   Manual verification is no longer required.
-   The script will run automatically using the saved cookies.

This manual step is required only once.

------------------------------------------------------------------------

## Poster Generation

After collecting specifications:

-   The script downloads a car image via Unsplash API.
-   Removes the background using remove.bg API.
-   Generates an 800x1200 poster layout.
-   Creates composition:
    -   brand (gray)
    -   model (black)
    -   central gray block
    -   centered vehicle image
    -   specifications block
    -   manufacturer country flag

The final result is saved as a PNG file.

------------------------------------------------------------------------

## Installation

### 1. Clone the repository

    git clone https://github.com/your-username/auto-poster-generator.git
    cd auto-poster-generator

### 2. Install dependencies

Python 3.9+ is recommended.

    pip install -r requirements.txt

Main dependencies:

-   requests
-   beautifulsoup4
-   selenium
-   undetected-chromedriver
-   pillow

------------------------------------------------------------------------

## Environment Variables (Optional)

You can define API keys via environment variables:

    export REMOVEBG_API_KEY=your_key
    export UNSPLASH_ACCESS_KEY=your_key

If remove.bg key is not provided, the original image will be used
without background removal.

------------------------------------------------------------------------

## Usage

Example:

    python auto_poster.py --car "Audi TT RS"

With custom output filename:

    python auto_poster.py --car "Porsche 911" --output poster.png

The generated poster will be saved in the current directory.

------------------------------------------------------------------------

## Project Structure

    auto_poster.py          # main script
    cookies_selenium.pkl    # saved cookies (created automatically after first verification)

------------------------------------------------------------------------

## Features

-   Fully automated parsing
-   Cloudflare bypass via undetected_chromedriver
-   One-time manual verification
-   Automatic cookie persistence
-   Fixed layout poster generation
-   Fallback specification database if parsing fails

------------------------------------------------------------------------

## Limitations

-   Requires installed Google Chrome
-   First run requires manual Cloudflare verification
-   Image quality depends on Unsplash API results
-   remove.bg has API usage limits

------------------------------------------------------------------------

## Purpose

This project was created as part of a technical test assignment:

-   automatic data scraping
-   poster generation based on reference
-   image export
-   focus on final visual result over tech stack

------------------------------------------------------------------------

Potential improvements:

-   image caching
-   enhanced parsing accuracy
-   multiple poster templates
-   extended country flag support
