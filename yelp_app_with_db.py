
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import re
import json
import time
import random
from io import BytesIO
import sqlite3
from datetime import datetime



# ============================================================
# SQLITE DATABASE
# ============================================================

# Permanent SQLite database. Reused across all scraping sessions.
# Existing records are never deleted automatically.
DB_NAME = "yelp_businesses.db"


def get_db_connection():
    """Create and return a SQLite database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Create the businesses table if it does not already exist."""
    conn = get_db_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            address TEXT,
            mobile_number TEXT,
            yelp_url TEXT NOT NULL UNIQUE,
            scraped_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def save_business_to_db(data):
    """
    Add a business to the permanent SQLite database.

    New Yelp URLs are appended as new records.
    If the same Yelp URL was scraped before, that existing record is
    updated instead of creating a duplicate.
    """
    conn = get_db_connection()

    yelp_url = str(data.get("Yelp URL", "")).strip()

    if not yelp_url:
        conn.close()
        return

    conn.execute(
        """
        INSERT INTO businesses (
            company_name,
            address,
            mobile_number,
            yelp_url,
            scraped_at
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(yelp_url) DO UPDATE SET
            company_name = excluded.company_name,
            address = excluded.address,
            mobile_number = excluded.mobile_number,
            scraped_at = excluded.scraped_at
        """,
        (
            data.get("Company Name", ""),
            data.get("Address", ""),
            data.get("Mobile Number", ""),
            yelp_url,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()


def get_database_records():
    """Return all stored businesses as a DataFrame."""
    conn = get_db_connection()

    df = pd.read_sql_query(
        """
        SELECT
            id AS ID,
            company_name AS "Company Name",
            address AS Address,
            mobile_number AS "Mobile Number",
            yelp_url AS "Yelp URL",
            scraped_at AS "Scraped At"
        FROM businesses
        ORDER BY id DESC
        """,
        conn
    )

    conn.close()
    return df


def get_database_count():
    """Return the number of businesses stored in the database."""
    conn = get_db_connection()

    result = conn.execute(
        "SELECT COUNT(*) FROM businesses"
    ).fetchone()

    conn.close()
    return result[0]


# Initialize database when the Streamlit app starts.
init_database()

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Yelp Business Scraper",
    page_icon="🔎",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .sub-title {
        color: #666666;
        font-size: 17px;
        margin-bottom: 25px;
    }

    .stButton > button {
        width: 100%;
        height: 48px;
        font-size: 17px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">🔎 Yelp Business Scraper</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'Extract company name, address and phone number from Yelp business listings.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Configuration")

    api_key = st.text_input(
        "ScraperAPI Key",
        type="password",
        placeholder="Enter your ScraperAPI key"
    )

    st.info(
        "Your API key is used only for the current session."
    )

    st.markdown("---")

    st.write("### Scraping Settings")

    delay_min = st.number_input(
        "Minimum delay (seconds)",
        min_value=1,
        max_value=10,
        value=2
    )

    delay_max = st.number_input(
        "Maximum delay (seconds)",
        min_value=1,
        max_value=15,
        value=4
    )


# ============================================================
# YELP URL INPUT
# ============================================================

st.subheader("1️⃣ Enter Yelp Search URL")

yelp_url = st.text_input(
    "Yelp Search URL",
    placeholder=(
        "https://www.yelp.com/search?"
        "find_desc=Trucking+Companies&"
        "find_loc=Los+Angeles%2C+CA"
    )
)


# ============================================================
# NUMBER OF COMPANIES
# ============================================================

st.subheader("2️⃣ Scraping Options")

col1, col2 = st.columns(2)

with col1:

    max_companies = st.number_input(
        "Maximum companies to scrape",
        min_value=1,
        max_value=300,
        value=30
    )

with col2:

    st.write("")
    st.write("")

    st.caption(
        "Each company requires an additional request "
        "to its Yelp business page."
    )


# ============================================================
# HELPER FUNCTION
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# FETCH PAGE USING SCRAPERAPI
# ============================================================

def fetch_page(url, api_key):

    params = {
        "api_key": api_key,
        "url": url,
        "premium": "true"
    }

    response = requests.get(
        "https://api.scraperapi.com/",
        params=params,
        timeout=120
    )

    if response.status_code != 200:

        raise Exception(
            f"ScraperAPI error "
            f"{response.status_code}: "
            f"{response.text[:300]}"
        )

    return response.text


# ============================================================
# EXTRACT PHONE NUMBER
# ============================================================

def extract_phone(soup):

    # --------------------------------------------------------
    # METHOD 1: tel: link
    # --------------------------------------------------------

    for link in soup.find_all(
        "a",
        href=True
    ):

        href = link.get(
            "href",
            ""
        )

        if href.startswith("tel:"):

            phone = href.replace(
                "tel:",
                ""
            ).strip()

            if phone:
                return phone


    # --------------------------------------------------------
    # METHOD 2: Search page text
    # --------------------------------------------------------

    text = soup.get_text(
        " ",
        strip=True
    )


    patterns = [

        r"\(\d{3}\)\s*\d{3}[-.\s]\d{4}",

        r"\d{3}[-.\s]\d{3}[-.\s]\d{4}",

        r"\d{3}\.\d{3}\.\d{4}"

    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:

            return match.group(0)


    return ""


# ============================================================
# EXTRACT ADDRESS
# ============================================================

def extract_address(soup):

    # --------------------------------------------------------
    # METHOD 1: <address> element
    # --------------------------------------------------------

    address = soup.find(
        "address"
    )


    if address:

        value = clean_text(
            address.get_text(
                " ",
                strip=True
            )
        )


        if value:

            return value


    # --------------------------------------------------------
    # METHOD 2: JSON-LD
    # --------------------------------------------------------

    scripts = soup.find_all(
        "script",
        type="application/ld+json"
    )


    for script in scripts:

        try:

            raw = (
                script.string
                or script.get_text()
            )


            if not raw:

                continue


            data = json.loads(
                raw
            )


            # JSON-LD can be a dictionary

            if isinstance(
                data,
                dict
            ):

                items = [data]


            # Or a list

            elif isinstance(
                data,
                list
            ):

                items = data


            else:

                continue


            for item in items:

                if not isinstance(
                    item,
                    dict
                ):

                    continue


                address_data = item.get(
                    "address"
                )


                if isinstance(
                    address_data,
                    dict
                ):

                    parts = []


                    for key in [

                        "streetAddress",

                        "addressLocality",

                        "addressRegion",

                        "postalCode"

                    ]:

                        value = address_data.get(
                            key
                        )


                        if value:

                            parts.append(
                                str(value)
                            )


                    if parts:

                        return ", ".join(
                            parts
                        )


        except Exception:

            continue


    return ""


# ============================================================
# EXTRACT BUSINESS NAME FROM SEARCH PAGE
# ============================================================

def extract_company_name(link):

    # --------------------------------------------------------
    # Try nearby headings
    # --------------------------------------------------------

    parent = link


    for _ in range(8):

        if parent.parent:

            parent = parent.parent


        heading = parent.find(
            ["h2", "h3", "h4"]
        )


        if heading:

            name = clean_text(
                heading.get_text(
                    " ",
                    strip=True
                )
            )


            if name:

                return name


    # --------------------------------------------------------
    # Fallback: link text
    # --------------------------------------------------------

    name = clean_text(
        link.get_text(
            " ",
            strip=True
        )
    )


    return name


# ============================================================
# EXTRACT SEARCH RESULTS
# ============================================================

def extract_search_results(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    companies = []

    seen_urls = set()


    # --------------------------------------------------------
    # Find Yelp business links
    # --------------------------------------------------------

    for link in soup.find_all(
        "a",
        href=True
    ):

        href = link.get(
            "href",
            ""
        )


        if "/biz/" not in href:

            continue


        # Remove query parameters

        href = href.split("?")[0]


        # Create complete URL

        business_url = urljoin(
            "https://www.yelp.com",
            href
        )


        # ----------------------------------------------------
        # Remove duplicates
        # ----------------------------------------------------

        if business_url in seen_urls:

            continue


        seen_urls.add(
            business_url
        )


        # ----------------------------------------------------
        # Get company name
        # ----------------------------------------------------

        company_name = extract_company_name(
            link
        )


        if not company_name:

            continue


        companies.append({

            "Company Name":
                company_name,

            "Yelp URL":
                business_url

        })


    return companies


# ============================================================
# SCRAPE INDIVIDUAL BUSINESS PAGE
# ============================================================

def scrape_business(
    company,
    api_key
):

    # --------------------------------------------------------
    # Load individual Yelp business page
    # --------------------------------------------------------

    html = fetch_page(
        company["Yelp URL"],
        api_key
    )


    # --------------------------------------------------------
    # Parse HTML
    # --------------------------------------------------------

    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    # --------------------------------------------------------
    # Extract address
    # --------------------------------------------------------

    address = extract_address(
        soup
    )


    # --------------------------------------------------------
    # Extract phone
    # --------------------------------------------------------

    phone = extract_phone(
        soup
    )


    return {

        "Company Name":
            company["Company Name"],

        "Address":
            address,

        "Mobile Number":
            phone,

        "Yelp URL":
            company["Yelp URL"]

    }


# ============================================================
# START SCRAPING BUTTON
# ============================================================

start_scraping = st.button(
    "🚀 Start Scraping",
    type="primary"
)


# ============================================================
# MAIN SCRAPING PROCESS
# ============================================================

if start_scraping:

    # ========================================================
    # VALIDATE API KEY
    # ========================================================

    if not api_key:

        st.error(
            "❌ Please enter your ScraperAPI key."
        )

        st.stop()


    # ========================================================
    # VALIDATE YELP URL
    # ========================================================

    if not yelp_url:

        st.error(
            "❌ Please enter a Yelp search URL."
        )

        st.stop()


    if "yelp.com/search" not in yelp_url:

        st.error(
            "❌ Please enter a valid Yelp search-results URL."
        )

        st.stop()


    # ========================================================
    # START
    # ========================================================

    st.divider()

    st.subheader(
        "🔄 Scraping in progress..."
    )


    progress = st.progress(
        0
    )


    status = st.empty()


    try:

        # ====================================================
        # STEP 1: LOAD YELP SEARCH PAGE
        # ====================================================

        status.write(
            "📡 Loading Yelp search results..."
        )


        search_html = fetch_page(
            yelp_url,
            api_key
        )


        # ====================================================
        # STEP 2: EXTRACT BUSINESS LINKS
        # ====================================================

        status.write(
            "🔍 Finding Yelp business listings..."
        )


        companies = extract_search_results(
            search_html
        )


        # ====================================================
        # CHECK RESULTS
        # ====================================================

        if not companies:

            st.error(
                "❌ No Yelp businesses were found."
            )


            st.info(
                "Please check the Yelp URL and try again."
            )


            st.stop()


        # ====================================================
        # LIMIT NUMBER OF COMPANIES
        # ====================================================

        companies = companies[
            :int(max_companies)
        ]


        st.success(
            f"✅ Found {len(companies)} businesses."
        )


        # ====================================================
        # STEP 3: SCRAPE EACH BUSINESS
        # ====================================================

        results = []


        total = len(
            companies
        )


        for index, company in enumerate(
            companies,
            start=1
        ):

            status.write(
                f"🔎 Scraping "
                f"{index}/{total}: "
                f"{company['Company Name']}"
            )


            try:

                # --------------------------------------------
                # Scrape business details
                # --------------------------------------------

                data = scrape_business(
                    company,
                    api_key
                )


                # --------------------------------------------
                # Save extracted data to SQLite database
                # --------------------------------------------

                save_business_to_db(data)

                results.append(
                    data
                )


            except Exception as e:

                # --------------------------------------------
                # Keep company even if details fail
                # --------------------------------------------

                results.append({

                    "Company Name":
                        company["Company Name"],

                    "Address":
                        "",

                    "Mobile Number":
                        "",

                    "Yelp URL":
                        company["Yelp URL"]

                })


                st.warning(
                    f"⚠️ Failed to scrape "
                    f"{company['Company Name']}: "
                    f"{str(e)[:150]}"
                )


            # ----------------------------------------------
            # Update progress
            # ----------------------------------------------

            progress.progress(
                index / total
            )


            # ----------------------------------------------
            # Random delay between requests
            # ----------------------------------------------

            if index < total:

                delay = random.uniform(
                    float(delay_min),
                    float(delay_max)
                )


                time.sleep(
                    delay
                )


        # ====================================================
        # SCRAPING COMPLETED
        # ====================================================

        status.success(
            "✅ Scraping completed successfully!"
        )


        progress.progress(
            1.0
        )


        # ====================================================
        # CREATE DATAFRAME
        # ====================================================

        df = pd.DataFrame(
            results
        )


        # ====================================================
        # RESULTS SECTION
        # ====================================================

        st.divider()

        st.subheader(
            "📊 Scraping Results"
        )


        # ====================================================
        # METRICS
        # ====================================================

        col1, col2, col3 = st.columns(
            3
        )


        with col1:

            st.metric(
                "Companies",
                len(df)
            )


        with col2:

            phone_count = (
                df["Mobile Number"]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
                .sum()
            )


            st.metric(
                "Phone Numbers",
                phone_count
            )


        with col3:

            address_count = (
                df["Address"]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
                .sum()
            )


            st.metric(
                "Addresses",
                address_count
            )


        # ====================================================
        # DISPLAY RESULTS
        # ====================================================

        display_df = df[
            [
                "Company Name",
                "Address",
                "Mobile Number"
            ]
        ]


        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )


        # ====================================================
        # EXCEL DOWNLOAD
        # ====================================================

        st.subheader(
            "📥 Export Results"
        )


        buffer = BytesIO()


        # IMPORTANT:
        # The buffer is passed as the excel_writer.
        # Do NOT call df.to_excel() without the buffer.

        df.to_excel(
            buffer,
            index=False,
            engine="openpyxl"
        )


        buffer.seek(0)


        st.download_button(
            label="⬇️ Download Excel",
            data=buffer,
            file_name="yelp_scraped_results.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )


        # ====================================================
        # DATABASE SECTION
        # ====================================================

        st.divider()

        st.subheader("🗄️ Stored Database Records")

        db_df = get_database_records()

        db_count = len(db_df)

        st.metric(
            "Total Businesses Stored",
            db_count
        )

        if not db_df.empty:

            st.dataframe(
                db_df,
                use_container_width=True,
                hide_index=True
            )

            # ----------------------------------------------
            # Download all database records
            # ----------------------------------------------

            db_buffer = BytesIO()

            db_df.to_excel(
                db_buffer,
                index=False,
                engine="openpyxl"
            )

            db_buffer.seek(0)

            st.download_button(
                label="⬇️ Download All Database Records",
                data=db_buffer,
                file_name="yelp_database_records.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                key="download_database_excel"
            )

        else:

            st.info("No businesses are currently stored in the database.")


    # ========================================================
    # GLOBAL ERROR HANDLER
    # ========================================================

    except Exception as e:

        st.error(
            f"❌ Scraping failed: {str(e)}"
        )