from flask import Flask, render_template, url_for, jsonify, request
from dash_apps import create_continents_dash, create_years_countries_dash, create_segments_countries_dash, create_years_segments_dash, create_years_segments_countries_dash
import io, os
import pandas as pd
import math


app = Flask(__name__)


#Register dash apps
create_continents_dash(app)
create_years_countries_dash(app)
create_segments_countries_dash(app)
create_years_segments_dash(app)
create_years_segments_countries_dash(app)



@app.route("/")
def home():
    return render_template("home.html")

@app.route("/stale-chart")
def stale_chart():
    charts = [
        {"name": "Publication Across Years", "image": "publication_year.png"},
        {"name": "Top 30 Journals", "image": "Top_30_Journals.png"},
        {"name": "Dimensions/Segments per Year", "image": "Segments_year_stacked.png"},
        {"name": "Dominant Keywords", "image": "Dominant_keywords.png"},
        {"name": "3-Way Venn Diagram", "image": "3-way-venn-diagram-pt.png"},
        {"name": "Bibliographic Coupling", "image": "image_not_generated.png"},
    ]
    return render_template("stale_chart.html", charts=charts)


# Individual chart modal routes
@app.route("/chart/<chart_name>")
def chart_modal(chart_name):
    charts = {
        "publication": {"name": "Publication Across Years", "image": "publication_year.png"},
        "journals": {"name": "Top 30 Journals", "image": "Top_30_Journals.png"},
        "dimensions": {"name": "Dimensions/Segments per Year", "image": "Segments_year_stacked.png"},
        "keywords": {"name": "Dominant Keywords", "image": "Dominant_keywords.png"},
        "venn": {"name": "3-Way Venn Diagram", "image": "3-way-venn-diagram-pt.png"},
        "keywordfrequencies": {
            "name": "Segments & Keyword Frequencies",
            "images": [
                "unique-to-people.png",
                "people-process.png",
                "people-technology.png",
                "unique-to-process.png",
                "process-technology.png",
                "AllthreeSegments.png",
            ],
        },
    }
    chart = charts.get(chart_name)
    if chart:
        if chart_name == "keywordfrequencies":
            images_html = "".join(
                [
                    f'<img src="{url_for("static", filename=image)}" alt="Horizontal Chart" class="horizontal-image">'
                    for image in chart["images"]
                ]
            )
            return f"""
            <div>
                <h1>{chart['name']}</h1>
                <div class="horizontal-images-container">{images_html}</div>
            </div>
            """
        return f"""
        <div>
            <img src="{url_for('static', filename=chart['image'])}" alt="{chart['name']}">
            <h1>{chart['name']}</h1>
            <p>Detailed description about the chart...</p>
        </div>
        """
    return "Chart not found", 404


@app.route("/interactive-charts")
def interactive_charts():
    charts = [
        {"name": "Continents & Countries", "route": "/dash/continents"},
        {"name": "3-Way Venn Diagram", "route": "/dash/venn"},
        {"name": "Years & Countries", "route": "/dash/years-countries"},
        {"name": "Segments & Countries", "route": "/dash/segments-countries"},
        {"name": "Years & Segments", "route": "/dash/years-segments"},
        {"name": "Years, Segments & Countries", "route": "/dash/years-segments-countries"},
    ]
    return render_template("interactive_charts.html", charts=charts)


@app.route("/couplinganalysis")
def bibliographic():
    # Load the Excel file for commonly cited papers
    commonly_cited_path = "data/commonly_cited.xlsx"
    commonly_cited_df = pd.read_excel(commonly_cited_path)

    # Group commonly cited papers by segments and keywords
    commonly_cited_grouped = commonly_cited_df.groupby("Segments")

    # Create data structure for commonly cited papers
    commonly_cited = []
    for segment, group in commonly_cited_grouped:
        keyword_details = {}
        for _, row in group.iterrows():
            keyword = row["Keywords"]
            if keyword not in keyword_details:
                keyword_details[keyword] = []

            # Ensure unique In_Text_Citation within the keyword
            if not any(citation['In_Text_Citation'] == row["In_Text_Citation"] for citation in keyword_details[keyword]):
                keyword_details[keyword].append({
                    "In_Text_Citation": row["In_Text_Citation"],
                    "DOI": row["DOI"],
                    "Title": row["Title"]
                })

        commonly_cited.append({
            "Segments": segment,
            "KeywordDetails": keyword_details
        })

    # Load the Excel file for top 80% cited papers
    top_cited_path = "data/top_80_cited.xlsx"
    top_cited_df = pd.read_excel(top_cited_path)

    # Remove duplicate entries based on In_Text_Citation
    top_cited_df = top_cited_df.drop_duplicates(subset=["In_Text_Citation"])

    # Prepare the top 80% data
    top_cited = [
        {
            "In_Text_Citation": row["In_Text_Citation"],
            "DOI": row["DOI"]
        }
        for _, row in top_cited_df.iterrows()
    ]

    return render_template(
        "commonly_cited.html",
        commonly_cited=commonly_cited,
        top_cited=top_cited
    )


# Load data function
def load_data(file_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    file_path = os.path.join(data_dir, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    data = pd.read_excel(file_path)
    required_columns = {"Classified", "Reference_no", "Title", "URL"}
    if not required_columns.issubset(data.columns):
        raise ValueError(f"The Excel file must contain these columns: {required_columns}")

    return data

# Load the Excel data
venn_data = load_data("pt-set-amalgamated-main-corrected_v2.xlsx")

# Route for modal data
@app.route("/venn/modal/<category_url>")
def get_modal_data(category_url):
    # Map category URLs to their full names
    classified_map = {
        "unique-people": "Unique-People",
        "unique-process": "Unique-Process",
        "unique-technology": "Unique-Technology",
        "people-process": "People-Process",
        "people-technology": "People-Technology",
        "process-technology": "Process-Technology",
        "all-three": "AllThreeSegments",
    }

    # Get the full name of the category
    category_name = classified_map.get(category_url)
    if not category_name:
        return jsonify({"error": "Invalid category"}), 404

    # Filter the data for the selected category
    filtered_data = venn_data[venn_data["Classified"] == category_name]

    if filtered_data.empty:
        # Handle cases where no data is found for the category
        return jsonify({
            "category_name": category_name,
            "data": [],
            "message": f"No papers classified in the '{category_name}' dimension.",
            "total_count": len(venn_data),
            "classified_count": 0,
            "percentage": 0.0,
        })

    # Prepare the data for the modal
    modal_data = filtered_data[["Reference_no", "Title", "URL"]].to_dict(orient="records")

    # Calculate total count and percentage
    classified_count = len(filtered_data)
    total_count = len(venn_data)
    percentage = round((classified_count / total_count) * 100, 2)

    return jsonify({
        "category_name": category_name,
        "data": modal_data,
        "message": None,  # No error message for valid data
        "total_count": total_count,
        "classified_count": classified_count,
        "percentage": percentage,
    })


@app.route("/interactive-charts/venn-diagram")
def venn_diagram():
    # Define the categories with their URL mappings
    categories = [
        {"name": "Unique to People", "url": "unique-people"},
        {"name": "Unique to Process", "url": "unique-process"},
        {"name": "Unique to Technology", "url": "unique-technology"},
        {"name": "People & Process", "url": "people-process"},
        {"name": "People & Technology", "url": "people-technology"},
        {"name": "Process & Technology", "url": "process-technology"},
        {"name": "All Three Segments", "url": "all-three"},
    ]

    return render_template("venn_diagram.html", categories=categories)



@app.route('/selected-papers')
def selected_papers():
    return render_template('selected_papers.html')

@app.route("/selected-papers/references")
def references():
    # Load the Excel file
    file_path = "data/output_with_citations.xlsx"
    df = pd.read_excel(file_path)

    # Pagination parameters
    items_per_page = 10
    page = request.args.get("page", default=1, type=int)
    total_items = len(df)
    total_pages = math.ceil(total_items / items_per_page)

    # Validate page
    page = max(1, min(page, total_pages))

    # Slice data for the current page
    start = (page - 1) * items_per_page
    end = start + items_per_page
    paginated_data = df.iloc[start:end]

    # Prepare data for rendering
    references = []
    for _, row in paginated_data.iterrows():
        citation = row.get("Citations", "Citation unavailable").strip()
        url = row.get("URL", "").strip()
        id_num = row.get('Reference_no', "").strip()
        references.append({"citation": citation, "url": url, "id_num": id_num})

    # Render template
    return render_template(
        "references.html",
        references=references,
        page=page,
        total_pages=total_pages,
    )


@app.route('/selected-papers/themes')
def abstract_themes():
    # Load Excel file
    file_path = os.path.join('data', 'pt-set-amalgamated-main-corrected_v2.xlsx')
    data = pd.read_excel(file_path)

    # Ensure columns exist and handle missing values
    required_columns = ["Reference_no", "Title", "Abstract", "Extracted Themes"]
    if not all(col in data.columns for col in required_columns):
        return "Error: Missing required columns in the Excel file.", 500

    # Replace NaN in Extracted Themes with an empty string
    data["Extracted Themes"] = data["Extracted Themes"].fillna("")

    # Convert data to list of dictionaries
    papers = data[["Reference_no", "Title", "Abstract", "Extracted Themes", "URL"]].to_dict(orient="records")

    # Add a flag to check if themes are missing (all rows should have themes)
    for paper in papers:
        paper["Has_Themes"] = bool(paper["Extracted Themes"].strip())

    return render_template('abstract_themes.html', papers=papers)


# Function to load synonyms from the themes_synonyms.xlsx file
def load_synonyms(theme):
    # Load the second Excel file (themes_synonyms.xlsx)
    file_path = "data/themes_synonyms.xlsx"
    df = pd.read_excel(file_path, sheet_name=None)

    synonyms = []
    # Iterate over the sheets (People, Process, Technology)
    for sheet_name, sheet_data in df.items():
        # Filter rows where the "Theme" matches the provided theme
        matched_rows = sheet_data[sheet_data['Theme'].str.contains(theme, case=False, na=False)]
        synonyms.extend(matched_rows['Synonym'].tolist())
    
    return synonyms

@app.route("/selected-papers/key-focus")
def key_focus_expansion():
    # Load the first Excel file (expanded_keyfocus.xlsx)
    file_path = "data/expanded_keyfocus.xlsx"
    df = pd.read_excel(file_path)

    # Process data into a structure suitable for rendering
    segments = []
    for _, row in df.iterrows():
        keywords = [keyword.strip() for keyword in row["Expanded Key Focus"].split(",")]
        segments.append({
            "Segment": row["Segments/Dimensions"],
            "Keywords": keywords
        })

    return render_template("key_focus.html", segments=segments)

@app.route("/get_synonyms/<keyword>", methods=["GET"])
def get_synonyms(keyword):
    # Fetch synonyms for the selected keyword from the second Excel file
    synonyms = load_synonyms(keyword)
    return jsonify({'synonyms': synonyms})




# Run the app
if __name__ == "__main__":
    # Bind the app to the Cloud Run PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host="0.0.0.0", port=port)
