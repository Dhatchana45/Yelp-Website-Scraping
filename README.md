# Yelp Business Scraper

A Python-based web scraping application built with **Streamlit, ScraperAPI, BeautifulSoup, and SQLite** to extract business information from Yelp search results and individual business pages. The application supports multi-page scraping, duplicate detection, persistent database storage, and Excel export.

## 🚀 Features

- **Multi-Page Scraping:** Automatically navigates through Yelp search result pages to collect more than 20–30 businesses when additional results are available.
- **Company Name Extraction:** Retrieves business names from Yelp listings.
- **Company Description Extraction:** Extracts available company descriptions from individual business pages.
- **Address Extraction:** Collects business addresses when available.
- **Phone Number Extraction:** Extracts publicly displayed business phone numbers.
- **Yelp URL Collection:** Stores the individual Yelp business page URL for each record.
- **ScraperAPI Integration:** Uses ScraperAPI to retrieve Yelp pages.
- **SQLite Database:** Saves scraped records locally and preserves existing data between scraping sessions.
- **Duplicate Detection:** Uses Yelp business URLs to identify duplicate records.
- **Excel Export:** Exports collected business information to an Excel file.
- **Streamlit Interface:** Provides a simple interface for entering search URLs, configuring scraping, and viewing results.

## 🛠️ Tech Stack

- **Programming Language:** Python
- **Frontend:** Streamlit
- **Web Scraping:** BeautifulSoup4
- **HTTP Requests:** Requests
- **Data Processing:** Pandas
- **Database:** SQLite
- **API Service:** ScraperAPI
- **Export Format:** Excel (XLSX)

## 📁 Project Structure

```text
yelp-business-scraper/
├── yelp_business_scraper_updated.py
├── requirements.txt
├── README.md
├── .gitignore
└── yelp_businesses.db   # Created locally when the app runs
```

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Replace `YOUR_USERNAME` and `YOUR_REPOSITORY` with your GitHub username and repository name.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install streamlit requests beautifulsoup4 pandas openpyxl
```

If a `requirements.txt` file is available, use:

```bash
pip install -r requirements.txt
```

### 4. Configure ScraperAPI

1. Create an account at [ScraperAPI](https://www.scraperapi.com/).
2. Obtain your API key.
3. Enter the API key in the application's designated input field.

Keep your API key private. Never commit API credentials to GitHub.

## ▶️ Run the Application

Start the Streamlit application using:

```bash
streamlit run yelp_business_scraper_updated.py
```

Open the local URL displayed in the terminal, usually:

```text
http://localhost:8501
```

## 📖 How to Use

1. Launch the Streamlit application.
2. Enter your ScraperAPI key.
3. Paste a Yelp search results URL, such as a URL for a particular business category and location.
4. Click **Start Scraping**.
5. The application collects business URLs from the accessible search result pages.
6. It visits individual business pages to extract available company details.
7. Review the extracted results in the application.
8. Download the results as an Excel file.
9. Access previously saved records through the local SQLite database.

## 📊 Data Fields

| Field | Description |
|---|---|
| Company Name | Name of the business |
| Company Description | Available description of the business |
| Address | Business address, when available |
| Mobile Number | Publicly listed business phone number |
| Yelp URL | Individual Yelp business page URL |
| Scraped At | Date and time the record was saved |

**Note:** Phone numbers and descriptions may be unavailable on some business pages. The extracted phone number is the publicly listed business contact number and is not necessarily a mobile number.

## 🗄️ Database Storage

The application uses SQLite to store scraped business records in `yelp_businesses.db`.

- New business URLs are added to the database.
- Previously stored records are preserved across scraping sessions.
- Duplicate Yelp URLs are handled using the database's uniqueness constraint.
- Existing records can be updated when the same business is scraped again.

The database file is generated locally when the application initializes. Back it up if you need to preserve your collected data.

## 📤 Excel Export

The application allows you to download scraped business records in Excel format for:

- Lead research
- Business directory creation
- Data analysis
- Contact information management
- Reporting and record keeping

## ⚠️ Limitations

- The number of businesses returned depends on Yelp's accessible search results and pagination.
- Scraping does not guarantee access to every business in Yelp's database.
- Descriptions, addresses, and phone numbers may be missing or restricted.
- ScraperAPI usage is subject to account limits, pricing, and request availability.
- Large scraping jobs may take time because each business page requires an additional request.

## 🔒 Responsible Use

Use this project for lawful research and business data collection. Follow Yelp's applicable Terms of Service, robots and access restrictions, privacy requirements, and ScraperAPI's terms. Respect request limits and avoid collecting or misusing personal information.

## 🔮 Future Improvements

- Add advanced filtering and search.
- Support CSV and JSON exports.
- Add retry handling and improved error logging.
- Improve extraction of company descriptions and contact details.
- Add dashboard metrics for collected business records.
- Support scheduled scraping and automated reports.

## 👨‍💻 Author

**Dhatchana Moorthy P.**

B.E. Computer Science and Engineering | 2025 Graduate

- GitHub: [Dhatchana45](https://github.com/Dhatchana45)

---

⭐ If you find this project useful, consider starring the repository!
