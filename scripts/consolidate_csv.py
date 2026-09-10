# MusGU+ table generator
# Generates the discovery table and model detail pages from YAML evaluations.

import datetime
import glob
import html
import os

import pandas as pd
import yaml
from bs4 import BeautifulSoup


UTC = getattr(datetime, "UTC", datetime.timezone.utc)


DIMENSIONS = [
    (
        "adaptability",
        [
            "hardware_requirements",
            "dataset_size",
            "adaptation_pathways",
            "technical_barriers",
            "model_redistribution",
        ],
    ),
    (
        "usability",
        [
            "interface_availability",
            "access_restrictions",
            "realtime_capabilities",
            "workflow_integration",
            "output_licensing",
            "community_support",
        ],
    ),
    (
        "controllability",
        [
            "conditioning_inputs",
            "time_varying_control",
            "feature_disentanglement",
            "control_parameters",
        ],
    ),
]

DIMENSION_LABELS = {
    "adaptability": "Adaptability",
    "usability": "Usability",
    "controllability": "Controllability",
}

VALUE_MAP = {"high": 1, "partial": 0.5, "low": 0, "": 0}

STATUS_META = {
    "high": {"label": "Fully supported", "symbol": "✔︎", "class_name": "high"},
    "partial": {"label": "Partially supported", "symbol": "~", "class_name": "partial"},
    "low": {"label": "Not supported", "symbol": "✘", "class_name": "low"},
    "": {"label": "Not evaluated", "symbol": "–", "class_name": "empty"},
}

CRITERION_INFO = {
    "hardware_requirements": {
        "table_label": "Hardware<br/>Requirements",
        "page_label": "Hardware Requirements",
        "id": "hardware",
    },
    "dataset_size": {
        "table_label": "Dataset<br/>Size",
        "page_label": "Dataset Size",
        "id": "dataset",
    },
    "adaptation_pathways": {
        "table_label": "Adaptation<br/>Pathways",
        "page_label": "Adaptation Pathways",
        "id": "adaptation",
    },
    "technical_barriers": {
        "table_label": "Technical<br/>Barriers",
        "page_label": "Technical Barriers",
        "id": "technical",
    },
    "model_redistribution": {
        "table_label": "Model<br/>Redistribution",
        "page_label": "Model Redistribution",
        "id": "redistribution",
    },
    "interface_availability": {
        "table_label": "Interface<br/>Availability",
        "page_label": "Interface Availability",
        "id": "interface",
    },
    "access_restrictions": {
        "table_label": "Access<br/>Restrictions",
        "page_label": "Access Restrictions",
        "id": "access",
    },
    "realtime_capabilities": {
        "table_label": "Real-time<br/>Capabilities",
        "page_label": "Real-time Capabilities",
        "id": "realtime",
    },
    "workflow_integration": {
        "table_label": "Workflow<br/>Integration",
        "page_label": "Workflow Integration",
        "id": "workflow",
    },
    "output_licensing": {
        "table_label": "Output<br/>Licensing",
        "page_label": "Output Licensing",
        "id": "licensing",
    },
    "community_support": {
        "table_label": "Community<br/>Support",
        "page_label": "Community Support",
        "id": "community",
    },
    "conditioning_inputs": {
        "table_label": "Conditioning<br/>Inputs",
        "page_label": "Conditioning Inputs",
        "id": "conditioning",
    },
    "time_varying_control": {
        "table_label": "Time-Varying<br/>Control",
        "page_label": "Time-Varying Control",
        "id": "timevarying",
    },
    "feature_disentanglement": {
        "table_label": "Feature<br/>Disentanglement",
        "page_label": "Feature Disentanglement",
        "id": "disentanglement",
    },
    "control_parameters": {
        "table_label": "Control<br/>Parameters",
        "page_label": "Control Parameters",
        "id": "parameters",
    },
}

SYNTHETIC_TAGS = {
    "hardware_requirements": {"high": ["CPU"], "partial": [], "low": []},
    "dataset_size": {"high": ["small dataset"], "partial": [], "low": []},
    "realtime_capabilities": {"high": ["real-time"], "partial": [], "low": []},
}


def split_tags(value):
    if not value or not isinstance(value, str):
        return []
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def escape_attr(value):
    return html.escape(str(value), quote=True)


def create_dataframe(files):
    df = pd.DataFrame()
    source_file = []
    project_slugs = []

    for file_name in files:
        with open(file_name, "r", encoding="utf-8") as file:
            file_df = pd.json_normalize(yaml.safe_load(file))
        source_file.append(file_name[1:])
        project_slugs.append(os.path.splitext(os.path.basename(file_name))[0])
        df = pd.concat([df, file_df], axis=0)

    df["source.file"] = source_file
    df["project.slug"] = project_slugs
    df = df.replace({None: ""})
    df = df[df["project.name"] != ""]
    df.set_index("project.name", inplace=True)
    return df


def calculate_scores(df):
    for project in df.index:
        for dimension_key, criteria in DIMENSIONS:
            columns = [f"{dimension_key}.{criterion}.value" for criterion in criteria]
            score = sum(VALUE_MAP.get(df.loc[project, column], 0) for column in columns if column in df.columns)
            df.loc[project, f"{dimension_key}_score"] = round((score / len(criteria)) * 100, 0)

        overall = (
            df.loc[project, "adaptability_score"]
            + df.loc[project, "controllability_score"]
            + df.loc[project, "usability_score"]
        ) / 3
        df.loc[project, "overall_score"] = round(overall, 0)

    return df


def collect_all_applications(df):
    applications = set()
    for project in df.index:
        applications.update(split_tags(df.loc[project, "project.applications"]))
    return sorted(applications)


def collect_tags_by_criterion(df):
    tags_by_criterion = {}

    for project in df.index:
        for dimension_key, criteria in DIMENSIONS:
            for criterion in criteria:
                criterion_key = f"{dimension_key}.{criterion}"
                tags_col = f"{dimension_key}.{criterion}.tags"
                for tag in split_tags(df.loc[project, tags_col]) if tags_col in df.columns else []:
                    tags_by_criterion.setdefault(criterion_key, set()).add(tag)

                value_col = f"{dimension_key}.{criterion}.value"
                value = df.loc[project, value_col] if value_col in df.columns else ""
                for tag in SYNTHETIC_TAGS.get(criterion, {}).get(value, []):
                    tags_by_criterion.setdefault(criterion_key, set()).add(tag)

    for dimension_key, criteria in DIMENSIONS:
        for criterion in criteria:
            if criterion not in SYNTHETIC_TAGS:
                continue
            criterion_key = f"{dimension_key}.{criterion}"
            tags_by_criterion.setdefault(criterion_key, set())
            for value_level in ("high", "partial", "low"):
                tags_by_criterion[criterion_key].update(SYNTHETIC_TAGS[criterion].get(value_level, []))

    return tags_by_criterion


def get_row_tags(df, project):
    row_tags = []

    for dimension_key, criteria in DIMENSIONS:
        for criterion in criteria:
            criterion_id = CRITERION_INFO[criterion]["id"]
            tags_col = f"{dimension_key}.{criterion}.tags"
            for tag in split_tags(df.loc[project, tags_col]) if tags_col in df.columns else []:
                row_tags.append(f"{criterion_id}:{tag}")

            value_col = f"{dimension_key}.{criterion}.value"
            value = df.loc[project, value_col] if value_col in df.columns else ""
            for tag in SYNTHETIC_TAGS.get(criterion, {}).get(value, []):
                row_tags.append(f"{criterion_id}:{tag}")

    return row_tags


def get_status_meta(value):
    return STATUS_META.get(value or "", STATUS_META[""])


def build_detail_page_link(slug):
    return f"models/{slug}/"


def build_criterion_anchor(criterion):
    return CRITERION_INFO[criterion]["page_label"].lower().replace(" ", "-")


def build_criterion_page_link(slug, criterion):
    return f"{build_detail_page_link(slug)}#{build_criterion_anchor(criterion)}"


def write_html(df):
    projects = df.index.tolist()
    sorted_applications = collect_all_applications(df)
    tags_by_criterion = collect_tags_by_criterion(df)

    html_table = ['<table id="musgu-table">', "<thead>", '<tr class="main-header">']
    html_table.append('<th class="sortable" data-sort="name" data-type="text">Model <span class="sort-arrow">▴▾</span></th>')

    for dimension_key, criteria in DIMENSIONS:
        html_table.append(
            f'<th colspan="{len(criteria)}" class="sortable" data-sort="{dimension_key}" data-type="number">'
            '<div class="dimension-header-cell">'
            f'<span class="dimension-name">{DIMENSION_LABELS[dimension_key]} <span class="sort-arrow">▴▾</span></span>'
            f'<div class="dimension-filter-tag" data-filter="{dimension_key}" data-threshold="60">≥60%</div>'
            "</div></th>"
        )

    html_table.append("</tr>")
    html_table.append('<tr class="second-header">')
    html_table.append("<th></th>")

    for dimension_key, criteria in DIMENSIONS:
        for criterion in criteria:
            info = CRITERION_INFO[criterion]
            criterion_key = f"{dimension_key}.{criterion}"
            tags = sorted(tags_by_criterion.get(criterion_key, set()), key=len)

            header_bits = ['<th><div class="criterion-header-wrapper">', f'<span>{info["table_label"]}</span>']
            if tags:
                header_bits.append(f'<div class="criterion-tags" data-criterion="{info["id"]}">')
                for tag in tags:
                    escaped_tag = html.escape(tag)
                    header_bits.append(
                        f'<span class="criterion-tag" data-tag="{escaped_tag}" '
                        f'data-criterion="{info["id"]}">{escaped_tag}</span>'
                    )
                header_bits.append(f'<span class="expand-tags-btn" data-criterion="{info["id"]}">+0</span>')
                header_bits.append("</div>")
            header_bits.append("</div></th>")
            html_table.append("".join(header_bits))

    html_table.append("</tr>")
    html_table.append("</thead>")
    html_table.append("<tbody>")

    for project in projects:
        affiliation = df.loc[project, "project.affiliation"] if "project.affiliation" in df.columns else ""
        slug = str(df.loc[project, "project.slug"])
        row_tags = get_row_tags(df, project)
        row_applications = split_tags(df.loc[project, "project.applications"]) if "project.applications" in df.columns else []

        row_html = [
            f'<tr class="row-a" data-name="{escape_attr(project)}" '
            f'data-affiliation="{escape_attr(affiliation)}" '
            f'data-adaptability="{int(df.loc[project, "adaptability_score"])}" '
            f'data-usability="{int(df.loc[project, "usability_score"])}" '
            f'data-controllability="{int(df.loc[project, "controllability_score"])}" '
            f'data-overall="{int(df.loc[project, "overall_score"])}" '
            f'data-tags="{escape_attr(",".join(row_tags))}" '
            f'data-applications="{escape_attr(",".join(row_applications))}">'
        ]

        row_html.append('<td class="name-cell">')
        row_html.append(
            f'<div class="model-name"><a href="{escape_attr(build_detail_page_link(slug))}" '
            f'aria-label="Open details page for {escape_attr(project)}">{html.escape(project)}</a></div>'
        )
        if affiliation:
            row_html.append(f'<div class="affiliation">{html.escape(affiliation)}</div>')
        row_html.append("</td>")

        for dimension_key, criteria in DIMENSIONS:
            for criterion in criteria:
                value = df.loc[project, f"{dimension_key}.{criterion}.value"]
                notes = escape_attr(df.loc[project, f"{dimension_key}.{criterion}.notes"])
                status = get_status_meta(value)
                criterion_link = build_criterion_page_link(slug, criterion)
                criterion_label = CRITERION_INFO[criterion]["page_label"]
                row_html.append(
                    f'<td class="{status["class_name"]} data-cell" title="{notes}" '
                    f'data-detail-link="{escape_attr(criterion_link)}" role="link" tabindex="0" '
                    f'aria-label="Open {escape_attr(criterion_label)} details for {escape_attr(project)}">'
                    f'{status["symbol"]}</td>'
                )

        row_html.append("</tr>")
        html_table.append("".join(row_html))

    html_table.append("</tbody>")
    html_table.append("</table>")

    applications_html = ['<div class="applications-section">', '<h3 class="applications-title">Musical Applications</h3>']
    applications_html.append('<div class="applications-tags-container">')
    for app in sorted_applications:
        escaped_app = html.escape(app)
        applications_html.append(
            f'<span class="application-tag" data-application="{escaped_app}">{escaped_app}</span>'
        )
    applications_html.append("</div>")
    applications_html.append("</div>")

    return "\n".join(html_table), "\n".join(applications_html)


def create_index(table_html, applications_html):
    with open("./docs/template.html", "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), "html.parser")

    applications_wrapper = soup.find(id="applications-wrapper")
    if applications_wrapper and applications_html:
        applications_wrapper.append(BeautifulSoup(applications_html, "html.parser"))

    included_table = soup.find(id="included-table")
    if included_table:
        included_table.append(BeautifulSoup(table_html, "html.parser"))

    guide_paragraphs = soup.find(id="table-guide")
    if guide_paragraphs:
        paragraphs = guide_paragraphs.find_all("p")
        if paragraphs:
            paragraphs[-1].clear()
            paragraphs[-1].append("For the underlying evaluation files, explore the corresponding YAML entries in the ")
            link = soup.new_tag(
                "a",
                href="https://github.com/lauraibnz/MusGU-plus/tree/main/projects",
                style="color: #0066cc;",
            )
            link.string = "projects folder"
            paragraphs[-1].append(link)
            paragraphs[-1].append(".")

    build_message = datetime.datetime.now(UTC).strftime("Discovery tool last updated on %Y-%m-%d at %H:%M UTC.")
    target_footer = soup.find(id="build-time")
    if target_footer:
        target_footer.string = build_message

    with open("./docs/index.html", "w", encoding="utf-8") as file:
        file.write(str(soup))


def load_html_template(template_path):
    with open(template_path, "r", encoding="utf-8") as file:
        return BeautifulSoup(file.read(), "html.parser")


def render_link_list(project_row, slug):
    links = []
    link_specs = [
        ("🔗", "Website", project_row.get("project.link", "")),
        ("💻", "Repository", project_row.get("project.repository", "")),
        ("📄", "Article", project_row.get("project.article", "")),
        ("⬇️", "Checkpoints", project_row.get("project.checkpoints", "")),
        ("🎹", "UI", project_row.get("project.ui", "")),
    ]

    for icon, label, url in link_specs:
        clean_url = str(url).strip()
        if not clean_url or clean_url.lower().startswith("not available"):
            continue
        links.append(
            f'<a class="resource-link" href="{escape_attr(clean_url)}" '
            f'target="_blank" rel="noreferrer noopener">'
            f'<span class="resource-link-icon" aria-hidden="true">{html.escape(icon)}</span>'
            f'<span class="resource-link-label">{html.escape(label)}</span>'
            f"</a>"
        )

    return "".join(links)


def render_applications(applications):
    if not applications:
        return '<p class="applications-copy">No musical applications listed.</p>'
    return f'<p class="applications-copy">{html.escape(", ".join(applications))}</p>'


def render_criterion_card(project_row, dimension_key, criterion):
    value = project_row.get(f"{dimension_key}.{criterion}.value", "")
    notes = project_row.get(f"{dimension_key}.{criterion}.notes", "")
    tags = split_tags(project_row.get(f"{dimension_key}.{criterion}.tags", ""))
    status = get_status_meta(value)
    info = CRITERION_INFO[criterion]
    criterion_id = build_criterion_anchor(criterion)
    notes_html = html.escape(notes) if notes else "No notes provided."
    tags_html = ""
    if tags:
        tag_chips = "".join(
            f'<span class="criterion-tag-chip">{html.escape(tag)}</span>' for tag in tags
        )
        tags_html = (
            '<div class="criterion-card-tags" aria-label="Tags">'
            '<span class="criterion-tags-label">Tags:</span>'
            f"{tag_chips}</div>"
        )

    return f"""
    <article class="criterion-card" id="{criterion_id}" tabindex="-1">
      <div class="criterion-card-top">
        <h3>{html.escape(info["page_label"])}</h3>
        <span class="status-pill {status["class_name"]}">{status["symbol"]} {html.escape(status["label"])}</span>
      </div>
      <p class="criterion-notes">{notes_html}</p>
      {tags_html}
    </article>
    """


def render_dimension_section(project_row, dimension_key, criteria):
    cards = "".join(render_criterion_card(project_row, dimension_key, criterion) for criterion in criteria)
    dimension_label = DIMENSION_LABELS[dimension_key]
    score = int(project_row.get(f"{dimension_key}_score", 0))

    return f"""
    <section class="detail-section" aria-labelledby="{dimension_key}-title">
      <div class="section-heading">
        <h2 id="{dimension_key}-title">{html.escape(dimension_label)}</h2>
        <div class="score-badge" aria-label="{html.escape(dimension_label)} summary {score} percent">{score}%</div>
      </div>
      <div class="criterion-grid">
        {cards}
      </div>
    </section>
    """


def render_model_page(project_name, project_row):
    slug = project_row["project.slug"]
    applications = split_tags(project_row.get("project.applications", ""))
    architecture = project_row.get("project.architecture", "")
    affiliation = project_row.get("project.affiliation", "")
    summary_note = project_row.get("project.notes", "")

    soup = load_html_template("./docs/model_template.html")

    page_title = soup.find(id="page-title")
    if page_title:
        page_title.string = f"MusGU+ Evaluation: {project_name}"

    page_heading = soup.find(id="model-page-heading")
    if page_heading:
        page_heading.string = f"MusGU+ Evaluation: {project_name}"

    yaml_source_link = soup.find(id="yaml-source-link")
    if yaml_source_link:
        yaml_source_link["href"] = f"https://github.com/lauraibnz/MusGU-plus/blob/main/projects/{slug}.yaml"

    model_affiliation = soup.find(id="model-affiliation")
    if model_affiliation:
        model_affiliation.string = affiliation or "Not provided"

    model_architecture = soup.find(id="model-architecture")
    if model_architecture:
        model_architecture.string = architecture or "Not provided"

    project_note = soup.find(id="project-note")
    if project_note:
        if summary_note:
            project_note.append(BeautifulSoup(f"<p>{html.escape(summary_note)}</p>", "html.parser"))
        else:
            project_note.decompose()

    resource_links = soup.find(id="resource-links")
    links_html = render_link_list(project_row, slug)
    if resource_links:
        if links_html:
            resource_links.append(BeautifulSoup(links_html, "html.parser"))
        else:
            resource_links.decompose()

    applications_content = soup.find(id="applications-content")
    if applications_content:
        applications_content.append(BeautifulSoup(render_applications(applications), "html.parser"))

    sections_html = "".join(
        render_dimension_section(project_row, dimension_key, criteria)
        for dimension_key, criteria in DIMENSIONS
    )
    dimension_sections = soup.find(id="dimension-sections")
    if dimension_sections:
        dimension_sections.append(BeautifulSoup(sections_html, "html.parser"))

    build_time = soup.find(id="build-time")
    if build_time:
        build_time.string = (
            "Model page last updated on "
            + datetime.datetime.now(UTC).strftime("%Y-%m-%d at %H:%M UTC")
            + "."
        )

    return str(soup)


def create_model_pages(df):
    os.makedirs("./docs/models", exist_ok=True)

    for project in df.index:
        project_row = df.loc[project].to_dict()
        slug = project_row["project.slug"]
        page_dir = os.path.join("./docs/models", slug)
        os.makedirs(page_dir, exist_ok=True)

        with open(os.path.join(page_dir, "index.html"), "w", encoding="utf-8") as file:
            file.write(render_model_page(project, project_row))


def main():
    path = "./projects"
    all_files = [file_name for file_name in glob.glob(path + "/*.yaml") if "_template" not in file_name]

    print("Processing files:", all_files)

    df = create_dataframe(all_files)
    df = calculate_scores(df)
    df = df.sort_values(by="overall_score", ascending=False)

    table_html, applications_html = write_html(df)
    create_index(table_html, applications_html)
    create_model_pages(df)
    df.to_csv("./docs/df.csv", index=False)

    print("✓ Table and model pages generated successfully!")


if __name__ == "__main__":
    main()
