import asyncio 
from flask import Flask, render_template, request, redirect, url_for, session
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = "333"  # Needed for sessions

BASE_URL = "https://tools.myfooddata.com/nutrition-facts/"

# Recommended Daily Intake values (example values)
RDI = {
    "Calories": 2000,
    "Total Fat": 70,
    "Saturated Fat": 20,
    "Cholesterol": 300,
    "Sodium": 2300,
    "Carbohydrates": 300,
    "Fiber": 30,
    "Sugars": 50,
    "Protein": 50
}

async def search_food(food_name):
    """Scrapes the search results for food suggestions."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(BASE_URL, wait_until="domcontentloaded")

        search_box = await page.query_selector("input[type='text']")
        if search_box:
            await search_box.fill(food_name)
            await search_box.press("Enter")

        try:
            await page.wait_for_selector("a.searchheading", timeout=10000)  # Wait for results
            elements = await page.query_selector_all("a.searchheading")
            suggestions = [
                {"name": await e.inner_text(), "url": await e.get_attribute("href")}
                for e in elements
            ]
            suggestions = suggestions[:10]  # Only return the top 10
        except Exception as e:
            suggestions = []  # No results or error

        await browser.close()
        return suggestions

async def scrape_nutrition(food_url):
    """Scrapes nutrition facts from a specific food page and returns the HTML table."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(food_url, wait_until="domcontentloaded")
        content = await page.content()
        await browser.close()

        soup = BeautifulSoup(content, "html.parser")
        table = soup.find("table")
        if table:
            return str(table)
        return "⚠️ No nutrition facts found."

def parse_nutrition_table(html_table):
    """
    Parses a nutrition facts table (HTML) and returns a dictionary of nutrient: value.
    This simple parser assumes each <tr> contains two <td> tags: nutrient and amount.
    """
    nutrient_totals = {}
    soup = BeautifulSoup(html_table, "html.parser")
    rows = soup.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            nutrient = cols[0].get_text(strip=True)
            try:
                # Remove any non-digit characters (except dot) and convert to float.
                value = float(''.join(ch for ch in cols[1].get_text() if ch.isdigit() or ch=='.'))
            except ValueError:
                value = 0.0
            # Sum up if the nutrient already exists
            nutrient_totals[nutrient] = nutrient_totals.get(nutrient, 0.0) + value
    return nutrient_totals

@app.route("/", methods=["GET", "POST"])
def home():
    suggestions = []
    if request.method == "POST":
        food_name = request.form.get("food_name")
        suggestions = asyncio.run(search_food(food_name))
    return render_template("index.html", suggestions=suggestions)

@app.route("/add_food")
def add_food():
    """Adds a food URL to the session-selected list."""
    food_url = request.args.get("url")
    if not food_url:
        return "⚠️ No food selected!"
    if "selected_foods" not in session:
        session["selected_foods"] = []
    if food_url not in session["selected_foods"]:
        selected = session["selected_foods"]
        selected.append(food_url)
        session["selected_foods"] = selected
    return redirect(url_for("home"))

@app.route("/calculate")
def calculate():
    """Scrapes each saved food concurrently, aggregates nutrition facts, and calculates daily percentages."""
    if "selected_foods" not in session or not session["selected_foods"]:
        return "⚠️ No foods have been selected!"

    async def aggregate_all():
        tasks = [scrape_nutrition(url) for url in session["selected_foods"]]
        results = await asyncio.gather(*tasks)
        aggregated = {}
        for table_html in results:
            if "No nutrition facts" not in table_html:
                nutrients = parse_nutrition_table(table_html)
                for nutrient, value in nutrients.items():
                    aggregated[nutrient] = aggregated.get(nutrient, 0.0) + value
        return aggregated

    aggregated = asyncio.run(aggregate_all())
    session["selected_foods"] = []  # Optionally clear the session once calculated

    # Create table rows with percentages if available
    table_rows = ""
    for nutrient, total in aggregated.items():
        percent_display = ""
        if nutrient in RDI and RDI[nutrient] > 0:
            percent = (total / RDI[nutrient]) * 100
            percent_display = f" ({percent:.1f}%)"
        table_rows += f"<tr><td>{nutrient }</td><td>{total}{percent_display}</td></tr>"
    nutrition_table = f"<table><tr><th>Nutrient</th><th>Total (Daily %)</th></tr>{table_rows}</table>"
    return render_template("nutrition.html", nutrition_data=nutrition_table)

if __name__ == "__main__":
    app.run(debug=True)
