// ============================================================
// PROJECT MODAL
// ============================================================

function openProjectModal() {

    const modal =
        document.getElementById("projectModal");

    if (modal) {
        modal.style.display = "flex";
    }
}


function closeProjectModal() {

    const modal =
        document.getElementById("projectModal");

    if (modal) {
        modal.style.display = "none";
    }
}


// ============================================================
// CREATE DETAIL FIELD
// ============================================================

function createDetailField(
    fieldName,
    fieldValue = "",
    removable = false
) {

    const container =
        document.getElementById(
            "detailsContainer"
        );


    const fieldWrapper =
        document.createElement("div");

    fieldWrapper.className =
        "detail-field";


    const header =
        document.createElement("div");

    header.className =
        "detail-field-header";


    const label =
        document.createElement("label");

    label.textContent =
        fieldName;


    header.appendChild(label);


    // Delete button only for custom fields

    if (removable) {

        const deleteButton =
            document.createElement("button");

        deleteButton.type = "button";

        deleteButton.className =
            "delete-field-btn";

        deleteButton.textContent =
            "×";

        deleteButton.title =
            "Remove field";


        deleteButton.onclick =
            function () {

                fieldWrapper.remove();

            };


        header.appendChild(
            deleteButton
        );
    }


    const input =
        document.createElement("input");

    input.type = "text";

    input.className =
        "detail-input";

    input.dataset.fieldName =
        fieldName;

    input.value =
        fieldValue || "";

    input.placeholder =
        "Enter " + fieldName;


    fieldWrapper.appendChild(
        header
    );

    fieldWrapper.appendChild(
        input
    );


    container.appendChild(
        fieldWrapper
    );
}


// ============================================================
// INITIAL DEFAULT FIELDS
// ============================================================

const defaultFields = [

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

];


const detailsContainer =
    document.getElementById(
        "detailsContainer"
    );


if (detailsContainer) {

    defaultFields.forEach(
        function (field) {

            createDetailField(
                field
            );

        }
    );
}


// ============================================================
// ADD NEW FIELD
// ============================================================

function addNewField() {

    const fieldName =
        prompt(
            "Enter the new field name:"
        );


    if (!fieldName) {
        return;
    }


    const trimmedName =
        fieldName.trim();


    if (!trimmedName) {
        return;
    }


    // Check duplicate fields

    const existingFields =
        document.querySelectorAll(
            ".detail-input"
        );


    for (
        let i = 0;
        i < existingFields.length;
        i++
    ) {

        if (
            existingFields[i]
                .dataset
                .fieldName
                .toLowerCase()
            ===
            trimmedName.toLowerCase()
        ) {

            alert(
                "This field already exists."
            );

            return;
        }
    }


    createDetailField(
        trimmedName,
        "",
        true
    );
}


// ============================================================
// FILE NAME - TIMELINE
// ============================================================

const timelineFile =
    document.getElementById(
        "timelineFile"
    );


if (timelineFile) {

    timelineFile.addEventListener(
        "change",
        function () {

            const fileName =
                this.files.length
                    ? this.files[0].name
                    : "";


            document.getElementById(
                "timelineFileName"
            ).textContent =
                fileName;

        }
    );
}


// ============================================================
// FILE NAME - KICKOFF
// ============================================================

const kickoffFile =
    document.getElementById(
        "kickoffFile"
    );


if (kickoffFile) {

    kickoffFile.addEventListener(
        "change",
        function () {

            const fileName =
                this.files.length
                    ? this.files[0].name
                    : "";


            document.getElementById(
                "kickoffFileName"
            ).textContent =
                fileName;

        }
    );
}


// ============================================================
// TIMELINE UPLOAD
// ============================================================

const timelineForm =
    document.getElementById(
        "timelineForm"
    );


if (timelineForm) {

    timelineForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const formData =
                new FormData(this);


            const status =
                document.getElementById(
                    "timelineStatus"
                );


            status.textContent =
                "Uploading...";


            try {

                const response =
                    await fetch(
                        "/upload_timeline",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const data =
                    await response.json();


                status.textContent =
                    data.message;

            }
            catch (error) {

                status.textContent =
                    "Error uploading timeline.";

                console.error(error);

            }

        }
    );
}


// ============================================================
// KICKOFF UPLOAD + AUTOMATIC EXTRACTION
// ============================================================

const kickoffForm =
    document.getElementById(
        "kickoffForm"
    );


if (kickoffForm) {

    kickoffForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const formData =
                new FormData(this);


            const status =
                document.getElementById(
                    "kickoffStatus"
                );


            status.textContent =
                "Uploading PDF and extracting details...";


            try {

                const response =
                    await fetch(
                        "/upload_kickoff",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const data =
                    await response.json();


                status.textContent =
                    data.message;


                // ==========================================
                // AUTOMATICALLY POPULATE FIELDS
                // ==========================================

                if (
                    data.success &&
                    data.extracted_data
                ) {

                    populateExtractedDetails(
                        data.extracted_data
                    );

                }

            }
            catch (error) {

                status.textContent =
                    "Error processing kickoff PDF.";

                console.error(error);

            }

        }
    );
}


// ============================================================
// POPULATE EXTRACTED DETAILS
// ============================================================

function populateExtractedDetails(
    extractedData
) {

    const inputs =
        document.querySelectorAll(
            ".detail-input"
        );


    inputs.forEach(
        function (input) {

            const fieldName =
                input.dataset.fieldName;


            if (
                Object.prototype
                    .hasOwnProperty
                    .call(
                        extractedData,
                        fieldName
                    )
            ) {

                input.value =
                    extractedData[fieldName] || "";

            }

        }
    );


    // Scroll to details

    const section =
        document.querySelector(
            ".details-section"
        );


    if (section) {

        section.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }
}


// ============================================================
// SAVE DETAILS
// ============================================================

async function saveDetails() {

    const inputs =
        document.querySelectorAll(
            ".detail-input"
        );


    const details = [];


    inputs.forEach(
        function (input) {

            details.push({

                name:
                    input.dataset.fieldName,

                value:
                    input.value.trim()

            });

        }
    );


    const projectName =
        document.querySelector(
            'input[name="project_name"]'
        ).value;


    const status =
        document.getElementById(
            "detailsStatus"
        );


    status.textContent =
        "Saving...";


    try {

        const response =
            await fetch(
                "/save_details",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        project_name:
                            projectName,

                        details:
                            details

                    })

                }
            );


        const data =
            await response.json();


        status.textContent =
            data.message;

    }
    catch (error) {

        status.textContent =
            "Error saving details.";

        console.error(error);

    }
}


// ============================================================
// PHOTO PREVIEW
// ============================================================

const projectPhoto =
    document.getElementById(
        "projectPhoto"
    );


if (projectPhoto) {

    projectPhoto.addEventListener(
        "change",
        function () {

            const file =
                this.files[0];


            if (!file) {
                return;
            }


            document.getElementById(
                "photoFileName"
            ).textContent =
                file.name;


            const reader =
                new FileReader();


            reader.onload =
                function (event) {

                    const preview =
                        document.getElementById(
                            "photoPreview"
                        );


                    preview.src =
                        event.target.result;


                    document.getElementById(
                        "photoPreviewContainer"
                    ).style.display =
                        "block";

                };


            reader.readAsDataURL(file);

        }
    );
}


// ============================================================
// PHOTO UPLOAD
// ============================================================

const photoForm =
    document.getElementById(
        "photoForm"
    );


if (photoForm) {

    photoForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const formData =
                new FormData(this);


            const status =
                document.getElementById(
                    "photoStatus"
                );


            status.textContent =
                "Uploading...";


            try {

                const response =
                    await fetch(
                        "/upload_photo",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const data =
                    await response.json();


                status.textContent =
                    data.message;

            }
            catch (error) {

                status.textContent =
                    "Error uploading photo.";

                console.error(error);

            }

        }
    );
}// ============================================================
// LOAD SAVED PROJECT DETAILS
// ============================================================

// ============================================================
// LOAD SAVED PROJECT DETAILS
// ============================================================

async function loadSavedDetails() {

    const projectInput =
        document.querySelector(
            'input[name="project_name"]'
        );


    if (!projectInput) {
        return;
    }


    const projectName =
        projectInput.value;


    const container =
        document.getElementById(
            "detailsContainer"
        );


    if (!container) {
        return;
    }


    // ========================================================
    // STEP 1
    // ALWAYS CREATE THE 11 DEFAULT FIELDS
    // ========================================================

    container.innerHTML = "";


    defaultFields.forEach(
        function (field) {

            createDetailField(
                field,
                "",
                false
            );

        }
    );


    // ========================================================
    // STEP 2
    // GET SAVED DETAILS
    // ========================================================

    try {

        const response =
            await fetch(
                "/get_details/" +
                encodeURIComponent(
                    projectName
                )
            );


        const data =
            await response.json();


        // No saved details yet
        // Keep the default fields empty

        if (
            !data.success ||
            !data.details ||
            data.details.length === 0
        ) {

            return;

        }


        // ====================================================
        // STEP 3
        // PUT SAVED VALUES INTO EXISTING DEFAULT FIELDS
        // ====================================================

        data.details.forEach(
            function (detail) {

                const inputs =
                    document.querySelectorAll(
                        ".detail-input"
                    );


                let existingInput = null;


                inputs.forEach(
                    function (input) {

                        if (
                            input.dataset.fieldName
                                .toLowerCase()
                            ===
                            detail.name
                                .toLowerCase()
                        ) {

                            existingInput =
                                input;

                        }

                    }
                );


                // =================================================
                // EXISTING DEFAULT FIELD
                // =================================================

                if (existingInput) {

                    existingInput.value =
                        detail.value || "";

                }


                // =================================================
                // CUSTOM FIELD
                // =================================================

                else {

                    createDetailField(
                        detail.name,
                        detail.value || "",
                        true
                    );

                }

            }
        );

    }
    catch (error) {

        console.error(
            "Error loading saved details:",
            error
        );

    }
}


// ============================================================
// LOAD SAVED PROJECT PHOTO
// ============================================================

async function loadSavedPhoto() {

    const projectInput =
        document.querySelector(
            'input[name="project_name"]'
        );

    if (!projectInput) {
        return;
    }

    const projectName =
        projectInput.value;

    try {

        const response =
            await fetch(
                "/get_photo/" +
                encodeURIComponent(projectName)
            );

        const data =
            await response.json();

        console.log("Saved photo:", data);

        if (
            data.success &&
            data.url
        ) {

            const preview =
                document.getElementById(
                    "photoPreview"
                );

            const previewContainer =
                document.getElementById(
                    "photoPreviewContainer"
                );

            const photoFileName =
                document.getElementById(
                    "photoFileName"
                );

            if (preview) {
                preview.src = data.url;
            }

            if (photoFileName) {
                photoFileName.textContent =
                    data.filename;
            }

            if (previewContainer) {
                previewContainer.style.display =
                    "block";
            }
        }

    }
    catch (error) {

        console.error(
            "Error loading saved photo:",
            error
        );

    }
}
// ============================================================
// LOAD WHEN PROJECT PAGE OPENS
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadSavedDetails();
         loadSavedPhoto();

    }
);