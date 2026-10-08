from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os
import re
import json
from werkzeug.utils import secure_filename
from pypdf import PdfReader

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

UPLOAD_FOLDER = "uploads"

KICKOFF_FOLDER = os.path.join(UPLOAD_FOLDER, "kickoff")
TIMELINE_FOLDER = os.path.join(UPLOAD_FOLDER, "timeline")
PHOTO_FOLDER = os.path.join(UPLOAD_FOLDER, "photos")
DATA_FOLDER = os.path.join(UPLOAD_FOLDER, "data")

PROJECTS_FILE = "projects.json"

os.makedirs(KICKOFF_FOLDER, exist_ok=True)
os.makedirs(TIMELINE_FOLDER, exist_ok=True)
os.makedirs(PHOTO_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024


# ============================================================
# DEFAULT PROJECTS
# ============================================================

DEFAULT_PROJECTS = [
    "Yamaha VC01",
    "Project Alpha",
    "Project Beta"
]


# ============================================================
# LOAD PROJECTS
# ============================================================

def load_projects():

    if not os.path.exists(PROJECTS_FILE):

        save_projects(DEFAULT_PROJECTS)

        return DEFAULT_PROJECTS.copy()

    try:

        with open(
            PROJECTS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            projects = json.load(f)

        if isinstance(projects, list):

            return projects

    except Exception as e:

        print(
            "Error loading projects:",
            e
        )

    return DEFAULT_PROJECTS.copy()


# ============================================================
# SAVE PROJECTS
# ============================================================

def save_projects(projects):

    with open(
        PROJECTS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            projects,
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# PREDEFINED FIELDS
# ============================================================

DEFAULT_FIELDS = [
    "ECU / Family Name",
    "Housing",
    "Lead Variant",
    "Customer Name",
    "HW PJM",
    "AE / SW PJM",
    "Customer SOP Date",
    "Bosch SOP Date",
    "Pin Count",
    "HW QGC0",
    "HW QGC4"
]


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    projects = load_projects()

    return render_template(
        "index.html",
        projects=projects
    )


# ============================================================
# PROJECT PAGE
# ============================================================

@app.route("/project/<project_name>")
def project(project_name):

    projects = load_projects()

    if project_name not in projects:

        return "Project not found", 404

    return render_template(
        "project.html",
        project_name=project_name
    )


# ============================================================
# ADD NEW PROJECT
# ============================================================

@app.route("/add_project", methods=["POST"])
def add_project():

    project_name = request.form.get(
        "project_name"
    )

    if project_name:

        project_name = project_name.strip()

        projects = load_projects()

        if project_name not in projects:

            projects.append(
                project_name
            )

            save_projects(
                projects
            )

    return redirect(
        url_for("index")
    )


# ============================================================
# SERVE PROJECT PHOTO
# ============================================================

@app.route("/project_photo/<project_name>/<filename>")
def project_photo(project_name, filename):

    project_folder = os.path.join(
        PHOTO_FOLDER,
        secure_filename(project_name)
    )

    return send_from_directory(
        project_folder,
        filename
    )

# ============================================================
# PDF VALUE EXTRACTION
# ============================================================

def clean_value(value):

    if not value:
        return ""

    value = value.strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


def find_value(text, labels):

    for label in labels:

        pattern = (
            r"(?i)"
            + re.escape(label)
            + r"\s*[:\-]?\s*"
            + r"([^\n\r]+)"
        )

        match = re.search(
            pattern,
            text
        )

        if match:

            value = clean_value(
                match.group(1)
            )

            if value:
                return value

    return ""


# ============================================================
# EXACT LABEL VALUE EXTRACTION
# ============================================================

def find_exact_label_value(text, label):

    pattern = (
        r"(?im)^\s*"
        + re.escape(label)
        + r"\s*:\s*"
        + r"([^\n\r]+)"
    )

    match = re.search(
        pattern,
        text
    )

    if match:

        return clean_value(
            match.group(1)
        )

    return ""

# ============================================================
# EXTRACT KICKOFF PDF
# ============================================================

def extract_kickoff_data(filepath):

    extracted = {}

    try:

        reader = PdfReader(filepath)

        pages_text = []

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                pages_text.append(page_text)

        text = "\n".join(pages_text)

        print("\n================ PDF TEXT ================\n")
        print(text)
        print("\n===========================================\n")


        # ========================================================
        # ECU / FAMILY NAME
        # ========================================================

        extracted["ECU / Family Name"] = find_value(
            text,
            [
                "ECU Name"
            ]
        )


        # ========================================================
        # VARIANTS
        # ========================================================

        # From:
        # Description: 08W-330cc & 070-200cc
        #
        # We want:
        # 08W, 070

        # variant_match = re.search(
        #     r"(?i)Description\s*:\s*([^\n\r]+)",
        #     text
        # )

        # variants = ""

        # if variant_match:

        #     description = clean_value(
        #         variant_match.group(1)
        #     )

        #     found_variants = re.findall(
        #         r"\b(08W|070)\b",
        #         description,
        #         re.IGNORECASE
        #     )

        #     if found_variants:

        #         variants = ", ".join(
        #             dict.fromkeys(found_variants)
        #         )

        # extracted["Variants"] = variants


        # ========================================================
        # LEAD VARIANT
        # ========================================================

        extracted["Lead Variant"] = find_value(
            text,
            [
                "Lead variant"
            ]
        )


        # ========================================================
        # PROJECT DETAILS SECTION
        # ========================================================

        # We specifically extract from:
        #
        # Project brief – MG1CA030
        #
        # Project details:
        # ECU :
        # Customer :
        # Housing:
        # Pin count:
        #
        # This prevents "Customer Project Manager"
        # from being picked up.

        project_details_match = re.search(
            r"(?is)"
            r"Project details\s*:"
            r"(.*?)(?:Top\s+Risks\s*/\s*Problems\s*:)",
            text
        )

        project_details_text = ""

        if project_details_match:

            project_details_text = (
                project_details_match.group(1)
            )

            print(
                "\n========== PROJECT DETAILS ==========\n"
            )

            print(
                project_details_text
            )

            print(
                "\n=====================================\n"
            )


        # ========================================================
        # CUSTOMER NAME
        # ========================================================

        customer = ""

        if project_details_text:

            customer_match = re.search(
                r"(?im)"
                r"^\s*[^\S\r\n]*"
                r"(?:\s*)?"
                r"Customer\s*:\s*"
                r"([^\r\n]+)",
                project_details_text
            )

            if customer_match:

                customer = clean_value(
                    customer_match.group(1)
                )


        extracted["Customer Name"] = customer


        # ========================================================
        # HOUSING
        # ========================================================

        housing = ""

        if project_details_text:

            housing_match = re.search(
                r"(?im)"
                r"^\s*[^\S\r\n]*"
                r"(?:\s*)?"
                r"Housing\s*:\s*"
                r"([^\r\n]+)",
                project_details_text
            )

            if housing_match:

                housing = clean_value(
                    housing_match.group(1)
                )


        extracted["Housing"] = housing


        # ========================================================
        # PIN COUNT
        # ========================================================

        pin_count = ""

        if project_details_text:

            pin_match = re.search(
                r"(?im)"
                r"^\s*[^\S\r\n]*"
                r"(?:\s*)?"
                r"Pin\s*count\s*:\s*"
                r"([^\r\n]+)",
                project_details_text
            )

            if pin_match:

                pin_count = clean_value(
                    pin_match.group(1)
                )


        # Fallback if Project details section isn't found

        if not pin_count:

            pin_match = re.search(
                r"(?i)"
                r"\b(\d+)\s*pin\b"
                r"(?:\s*\([^)]+\))?",
                text
            )

            if pin_match:

                pin_count = clean_value(
                    pin_match.group(0)
                )


        extracted["Pin Count"] = pin_count


        # ========================================================
        # HW PJM
        # ========================================================

        # From Org chart:
        #
        # HW SPjM
        # Abbur Thammanna Gowda Pruthviraj

        hw_pjm = ""

        hw_match = re.search(
            r"(?is)"
            r"HW\s+SPjM\s*"
            r"([^\r\n]+)"
            r"(?:\r?\n|\s+)"
            r"(?:\(([^)]+)\))?",
            text
        )

        if hw_match:

            hw_pjm = clean_value(
                hw_match.group(1)
            )

        extracted["HW PJM"] = hw_pjm


        # ========================================================
        # AE / SW PJM
        # ========================================================

        ae_sw_pjm = ""

        sw_match = re.search(
            r"(?is)"
            r"SW\s+SPjM\s*"
            r"([^\r\n]+)",
            text
        )

        ae_match = re.search(
            r"(?is)"
            r"AE\s+SpJM\s*"
            r"([^\r\n]+)",
            text
        )

        sw_name = ""

        ae_name = ""

        if sw_match:
            sw_name = clean_value(
                sw_match.group(1)
            )

        if ae_match:
            ae_name = clean_value(
                ae_match.group(1)
            )

        if sw_name and ae_name:

            ae_sw_pjm = (
                "SW: " + sw_name +
                " | AE: " + ae_name
            )

        elif sw_name:

            ae_sw_pjm = (
                "SW: " + sw_name
            )

        elif ae_name:

            ae_sw_pjm = (
                "AE: " + ae_name
            )

        extracted["AE / SW PJM"] = ae_sw_pjm


        # ========================================================
        # CUSTOMER SOP DATE
        # ========================================================

        extracted["Customer SOP Date"] = find_value(
            text,
            [
                "Customer SOP Date",
                "Customer SOP"
            ]
        )


        # ========================================================
        # BOSCH SOP DATE
        # ========================================================

        extracted["Bosch SOP Date"] = find_value(
            text,
            [
                "Bosch SOP Date",
                "Bosch SOP"
            ]
        )


        # ========================================================
        # HW QGC0
        # ========================================================

        extracted["HW QGC0"] = find_value(
            text,
            [
                "HW QGC0",
                "QGC0",
                "HW-QGC0"
            ]
        )


        # ========================================================
        # HW QGC4
        # ========================================================

        extracted["HW QGC4"] = find_value(
            text,
            [
                "HW QGC4",
                "QGC4",
                "HW-QGC4"
            ]
        )


        # ========================================================
        # MAKE SURE ALL DEFAULT FIELDS EXIST
        # ========================================================

        for field in DEFAULT_FIELDS:

            if field not in extracted:

                extracted[field] = ""


        return extracted


    except Exception as e:

        print(
            "PDF extraction error:",
            e
        )

        return {
            field: ""
            for field in DEFAULT_FIELDS
        }

    extracted = {}

    try:

        reader = PdfReader(
            filepath
        )

        pages_text = []

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                pages_text.append(
                    page_text
                )

        text = "\n".join(
            pages_text
        )

        print(
            "\n================ PDF TEXT ================\n"
        )

        print(text)

        print(
            "\n===========================================\n"
        )


        extracted[
            "ECU / Family Name"
        ] = find_value(
            text,
            [
                "ECU Name",
                "ECU Name / Family Name",
                "ECU Family Name",
                "Family Name",
                "ECU"
            ]
        )


        extracted[
            "Variants"
        ] = find_value(
            text,
            [
                "Variants",
                "Variant"
            ]
        )

        extracted[
    "Housing"
] = find_exact_label_value(
    text,
    "Housing"
)

        extracted[
            "Lead Variant"
        ] = find_value(
            text,
            [
                "Lead Variant"
            ]
        )


        extracted[
    "Customer Name"
] = find_exact_label_value(
    text,
    "Customer"
)


        extracted[
            "HW PJM"
        ] = find_value(
            text,
            [
                "HW PJM",
                "Hardware PJM",
                "HW-PJM"
            ]
        )


        extracted[
            "AE / SW PJM"
        ] = find_value(
            text,
            [
                "AE / SW PJM",
                "AE/SW PJM",
                "AE PJM",
                "SW PJM"
            ]
        )


        extracted[
            "Customer SOP Date"
        ] = find_value(
            text,
            [
                "Customer SOP Date",
                "Customer SOP"
            ]
        )


        extracted[
            "Bosch SOP Date"
        ] = find_value(
            text,
            [
                "Bosch SOP Date",
                "Bosch SOP"
            ]
        )


        extracted[
            "Pin Count"
        ] = find_value(
            text,
            [
                "Pin Count",
                "Pin count",
                "Pins"
            ]
        )


        if not extracted[
            "Pin Count"
        ]:

            pin_match = re.search(
                r"(?i)\b(\d+)\s*pin\b",
                text
            )

            if pin_match:

                extracted[
                    "Pin Count"
                ] = (
                    pin_match.group(1)
                    + " pin"
                )


        extracted[
            "HW QGC0"
        ] = find_value(
            text,
            [
                "HW QGC0",
                "QGC0",
                "HW-QGC0"
            ]
        )


        extracted[
            "HW QGC4"
        ] = find_value(
            text,
            [
                "HW QGC4",
                "QGC4",
                "HW-QGC4"
            ]
        )


        for field in DEFAULT_FIELDS:

            if field not in extracted:

                extracted[field] = ""


        return extracted


    except Exception as e:

        print(
            "PDF extraction error:",
            e
        )

        return {
            field: ""
            for field in DEFAULT_FIELDS
        }


# ============================================================
# UPLOAD KICKOFF
# ============================================================

@app.route(
    "/upload_kickoff",
    methods=["POST"]
)
def upload_kickoff():

    file = request.files.get(
        "kickoff_pdf"
    )

    project_name = request.form.get(
        "project_name"
    )


    if not file or not file.filename:

        return jsonify({
            "success": False,
            "message": "No file selected"
        })


    if not file.filename.lower().endswith(
        ".pdf"
    ):

        return jsonify({
            "success": False,
            "message":
                "Only PDF files are allowed"
        })


    filename = secure_filename(
        file.filename
    )


    project_folder = os.path.join(
        KICKOFF_FOLDER,
        secure_filename(
            project_name
        )
    )

    os.makedirs(
        project_folder,
        exist_ok=True
    )


    filepath = os.path.join(
        project_folder,
        filename
    )


    file.save(filepath)


    extracted_data = extract_kickoff_data(
        filepath
    )


    return jsonify({

        "success": True,

        "message":
            "Kickoff PDF uploaded and extracted successfully.",

        "filename":
            filename,

        "extracted_data":
            extracted_data

    })


# ============================================================
# UPLOAD TIMELINE
# ============================================================

@app.route(
    "/upload_timeline",
    methods=["POST"]
)
def upload_timeline():

    file = request.files.get(
        "timeline_pdf"
    )

    project_name = request.form.get(
        "project_name"
    )


    if not file or not file.filename:

        return jsonify({
            "success": False,
            "message": "No file selected"
        })


    if not file.filename.lower().endswith(
        ".pdf"
    ):

        return jsonify({
            "success": False,
            "message":
                "Only PDF files are allowed"
        })


    filename = secure_filename(
        file.filename
    )


    project_folder = os.path.join(
        TIMELINE_FOLDER,
        secure_filename(
            project_name
        )
    )

    os.makedirs(
        project_folder,
        exist_ok=True
    )


    filepath = os.path.join(
        project_folder,
        filename
    )


    file.save(filepath)


    return jsonify({

        "success": True,

        "message":
            "Timeline PDF uploaded successfully",

        "filename":
            filename

    })


# ============================================================
# UPLOAD PHOTO
# ============================================================

@app.route(
    "/upload_photo",
    methods=["POST"]
)
def upload_photo():

    file = request.files.get(
        "project_photo"
    )

    project_name = request.form.get(
        "project_name"
    )


    if not file or not file.filename:

        return jsonify({
            "success": False,
            "message":
                "No photo selected"
        })


    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp"
    }


    extension = os.path.splitext(
        file.filename
    )[1].lower()


    if extension not in allowed_extensions:

        return jsonify({
            "success": False,
            "message":
                "Only image files are allowed"
        })


    filename = secure_filename(
        file.filename
    )


    project_folder = os.path.join(
        PHOTO_FOLDER,
        secure_filename(
            project_name
        )
    )

    os.makedirs(
        project_folder,
        exist_ok=True
    )


    filepath = os.path.join(
        project_folder,
        filename
    )


    file.save(filepath)


    return jsonify({

        "success": True,

        "message":
            "Photo uploaded successfully",

        "filename":
            filename

    })


# ============================================================
# GET SAVED PROJECT PHOTO
# ============================================================

# ============================================================
# GET SAVED PROJECT PHOTO
# ============================================================

@app.route("/get_photo/<project_name>")
def get_photo(project_name):

    project_folder = os.path.join(
        PHOTO_FOLDER,
        secure_filename(project_name)
    )

    if not os.path.exists(project_folder):
        return jsonify({
            "success": False
        })

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp"
    }

    for filename in os.listdir(project_folder):

        extension = os.path.splitext(
            filename
        )[1].lower()

        if extension in allowed_extensions:

            return jsonify({
                "success": True,
                "filename": filename,

                "url": url_for(
                    "project_photo",
                    project_name=project_name,
                    filename=filename
                )
            })

    return jsonify({
        "success": False
    })

    project_folder = os.path.join(
        PHOTO_FOLDER,
        secure_filename(project_name)
    )

    if not os.path.exists(project_folder):
        return jsonify({
            "success": False
        })

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp"
    }

    for filename in os.listdir(project_folder):

        extension = os.path.splitext(
            filename
        )[1].lower()

        if extension in allowed_extensions:

            return jsonify({
                "success": True,
                "filename": filename,

                # IMPORTANT
                "url": url_for(
                    "project_photo",
                    project_name=project_name,
                    filename=filename
                )
            })

    return jsonify({
        "success": False
    })

    project_folder = os.path.join(
        PHOTO_FOLDER,
        secure_filename(project_name)
    )

    if not os.path.exists(project_folder):
        return jsonify({
            "success": False
        })

    # Find the first saved image
    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp"
    }

    for filename in os.listdir(project_folder):

        extension = os.path.splitext(
            filename
        )[1].lower()

        if extension in allowed_extensions:

            return jsonify({
                "success": True,
                "filename": filename
            })

    return jsonify({
        "success": False
    })


# ============================================================
# SAVE DETAILS
# ============================================================

@app.route(
    "/save_details",
    methods=["POST"]
)
def save_details():

    data = request.get_json()

    project_name = data.get(
        "project_name"
    )

    details = data.get(
        "details",
        []
    )


    if not project_name:

        return jsonify({
            "success": False,
            "message":
                "Project name is missing."
        })


    project_folder = os.path.join(
        DATA_FOLDER,
        secure_filename(
            project_name
        )
    )

    os.makedirs(
        project_folder,
        exist_ok=True
    )


    filepath = os.path.join(
        project_folder,
        "details.json"
    )


    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            details,
            f,
            indent=4,
            ensure_ascii=False
        )


    return jsonify({

        "success": True,

        "message":
            "Details saved successfully."

    })


# ============================================================
# LOAD SAVED DETAILS
# ============================================================

@app.route(
    "/get_details/<project_name>"
)
def get_details(project_name):

    filepath = os.path.join(
        DATA_FOLDER,
        secure_filename(
            project_name
        ),
        "details.json"
    )


    if not os.path.exists(filepath):

        return jsonify({

            "success": True,

            "details": []

        })


    try:

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as f:

            details = json.load(f)


        return jsonify({

            "success": True,

            "details": details

        })


    except Exception as e:

        print(
            "Error loading details:",
            e
        )

        return jsonify({

            "success": False,

            "details": []

        })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )