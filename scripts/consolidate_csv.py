# MusGU+ table generator
# Generates interactive HTML table from YAML evaluations

import yaml
import glob
import pandas as pd
from bs4 import BeautifulSoup
import datetime


def create_dataframe(files):
    df = pd.DataFrame()
    source_file = []
    for fname in files:
        with open(fname, 'r', encoding='utf-8') as file:
            file_df = pd.json_normalize(yaml.safe_load(file))
        source_file.append(fname[1:])
        df = pd.concat([df, file_df], axis=0)
    df["source.file"] = source_file
    df = df.replace({None: ""})
    df = df[df["project.name"] != ""]
    df.set_index("project.name", inplace=True)
    return df


def calculate_scores(df):
    """Calculate dimension scores for Adaptability, Controllability, Usability
    Scoring: high=1, partial=0.5, low=0
    """
    value_map = {'high': 1, 'partial': 0.5, 'low': 0, '': 0}
    
    for project in df.index:
        # Adaptability score (5 criteria)
        adapt_cols = [
            'adaptability.hardware_requirements.value',
            'adaptability.dataset_size.value',
            'adaptability.adaptation_pathways.value',
            'adaptability.technical_barriers.value',
            'adaptability.model_redistribution.value'
        ]
        adapt_score = sum(value_map.get(df.loc[project, col], 0) for col in adapt_cols if col in df.columns)
        adapt_max = len(adapt_cols)  # max possible score
        df.loc[project, 'adaptability_score'] = round((adapt_score / adapt_max) * 100, 0)
        
        # Controllability score (4 criteria)
        control_cols = [
            'controllability.conditioning_inputs.value',
            'controllability.time_varying_control.value',
            'controllability.feature_disentanglement.value',
            'controllability.control_parameters.value'
        ]
        control_score = sum(value_map.get(df.loc[project, col], 0) for col in control_cols if col in df.columns)
        control_max = len(control_cols)
        df.loc[project, 'controllability_score'] = round((control_score / control_max) * 100, 0)
        
        # Usability score (6 criteria)
        usability_cols = [
            'usability.interface_availability.value',
            'usability.access_restrictions.value',
            'usability.realtime_capabilities.value',
            'usability.workflow_integration.value',
            'usability.output_licensing.value',
            'usability.community_support.value'
        ]
        usability_score = sum(value_map.get(df.loc[project, col], 0) for col in usability_cols if col in df.columns)
        usability_max = len(usability_cols)
        df.loc[project, 'usability_score'] = round((usability_score / usability_max) * 100, 0)
        
        # Overall score (average of three dimensions)
        overall = (df.loc[project, 'adaptability_score'] + 
                   df.loc[project, 'controllability_score'] + 
                   df.loc[project, 'usability_score']) / 3
        df.loc[project, 'overall_score'] = round(overall, 0)
    
    return df


def write_html(df):
    # Collect all unique applications from all projects
    all_applications = set()
    projects = df.index.tolist()
    for p in projects:
        if 'project.applications' in df.columns:
            apps = df.loc[p, 'project.applications']
            if apps and isinstance(apps, str):
                app_list = [a.strip() for a in apps.split(',')]
                all_applications.update(app_list)
    
    # Sort applications alphabetically
    sorted_applications = sorted(all_applications)
    
    # Value-based synthetic tags mapping
    # Maps criterion → {value_level → [tag_names]}
    # These tags are automatically applied based on the score value
    synthetic_tags = {
        'hardware_requirements': {
            'high': ['CPU'],
            'partial': [],
            'low': []
        },
        'dataset_size': {
            'high': ['small dataset'],
            'partial': [],
            'low': []
        },
        'realtime_capabilities': {
            'high': ['real-time'],
            'partial': [],
            'low': []
        },
        # Add more criterion mappings here as needed
        # Example:
        # 'access_restrictions': {
        #     'high': ['free', 'open-access'],
        #     'partial': ['limited-access'],
        #     'low': ['restricted']
        # }
    }
    
    html_table = '<table id="musgu-table">\n'
    html_table += '<thead>\n'
    html_table += '<tr class="main-header">'
    html_table += '<th class="sortable" data-sort="name" data-type="text">Model <span class="sort-arrow">▴▾</span></th>'
    
    # Adaptability with dimension filter tag inline to the right
    html_table += '<th colspan="5" class="sortable" data-sort="adaptability" data-type="number">'
    html_table += '<div class="dimension-header-cell">'
    html_table += '<span class="dimension-name">Adaptability <span class="sort-arrow">▴▾</span></span>'
    html_table += '<div class="dimension-filter-tag" data-filter="adaptability" data-threshold="60">≥60%</div>'
    html_table += '</div></th>'
    
    # Usability with dimension filter tag inline to the right
    html_table += '<th colspan="6" class="sortable" data-sort="usability" data-type="number">'
    html_table += '<div class="dimension-header-cell">'
    html_table += '<span class="dimension-name">Usability <span class="sort-arrow">▴▾</span></span>'
    html_table += '<div class="dimension-filter-tag" data-filter="usability" data-threshold="60">≥60%</div>'
    html_table += '</div></th>'
    
    # Controllability with dimension filter tag inline to the right
    html_table += '<th colspan="4" class="sortable" data-sort="controllability" data-type="number">'
    html_table += '<div class="dimension-header-cell">'
    html_table += '<span class="dimension-name">Controllability <span class="sort-arrow">▴▾</span></span>'
    html_table += '<div class="dimension-filter-tag" data-filter="controllability" data-threshold="60">≥60%</div>'
    html_table += '</div></th>'
    
    html_table += '</tr>\n'
    
    # Second header with criterion names and filter icons
    html_table += '<tr class="second-header">'
    html_table += '<th></th>'  # Empty cell for Model column only
    
    # Collect tags by criterion for popups
    projects = df.index.tolist()
    tags_by_criterion = {}
    
    for p in projects:
        for dimension in ['adaptability', 'usability', 'controllability']:
            if dimension == 'adaptability':
                criteria = ['hardware_requirements', 'dataset_size', 'adaptation_pathways', 'technical_barriers', 'model_redistribution']
            elif dimension == 'usability':
                criteria = ['interface_availability', 'access_restrictions', 'realtime_capabilities', 'workflow_integration', 'output_licensing', 'community_support']
            else:
                criteria = ['conditioning_inputs', 'time_varying_control', 'feature_disentanglement', 'control_parameters']
            
            for criterion in criteria:
                criterion_key = f'{dimension}.{criterion}'
                
                # Collect explicit tags from YAML
                tags_col = f'{dimension}.{criterion}.tags'
                if tags_col in df.columns:
                    tags_val = df.loc[p, tags_col]
                    if tags_val and isinstance(tags_val, str):
                        tags_list = [t.strip() for t in tags_val.split(',')]
                        if criterion_key not in tags_by_criterion:
                            tags_by_criterion[criterion_key] = set()
                        tags_by_criterion[criterion_key].update(tags_list)
                
                # Add synthetic tags based on value level
                if criterion in synthetic_tags:
                    value_col = f'{dimension}.{criterion}.value'
                    if value_col in df.columns:
                        value = df.loc[p, value_col]
                        if value in synthetic_tags[criterion]:
                            synthetic_tag_list = synthetic_tags[criterion][value]
                            if synthetic_tag_list:
                                if criterion_key not in tags_by_criterion:
                                    tags_by_criterion[criterion_key] = set()
                                tags_by_criterion[criterion_key].update(synthetic_tag_list)
    
    # Add all possible synthetic tags to criterion tag sets (even if no projects currently have them)
    for dimension in ['adaptability', 'usability', 'controllability']:
        if dimension == 'adaptability':
            criteria = ['hardware_requirements', 'dataset_size', 'adaptation_pathways', 'technical_barriers', 'model_redistribution']
        elif dimension == 'usability':
            criteria = ['interface_availability', 'access_restrictions', 'realtime_capabilities', 'workflow_integration', 'output_licensing', 'community_support']
        else:
            criteria = ['conditioning_inputs', 'time_varying_control', 'feature_disentanglement', 'control_parameters']
        
        for criterion in criteria:
            if criterion in synthetic_tags:
                criterion_key = f'{dimension}.{criterion}'
                if criterion_key not in tags_by_criterion:
                    tags_by_criterion[criterion_key] = set()
                # Add all possible synthetic tags for this criterion
                for value_level in ['high', 'partial', 'low']:
                    if value_level in synthetic_tags[criterion]:
                        tags_by_criterion[criterion_key].update(synthetic_tags[criterion][value_level])
    
    # Criterion mapping for display names and IDs
    criterion_info = {
        'hardware_requirements': ('Hardware<br/>Requirements', 'hardware'),
        'dataset_size': ('Dataset<br/>Size', 'dataset'),
        'adaptation_pathways': ('Adaptation<br/>Pathways', 'adaptation'),
        'technical_barriers': ('Technical<br/>Barriers', 'technical'),
        'model_redistribution': ('Model<br/>Redistribution', 'redistribution'),
        'interface_availability': ('Interface<br/>Availability', 'interface'),
        'access_restrictions': ('Access<br/>Restrictions', 'access'),
        'realtime_capabilities': ('Real-time<br/>Capabilities', 'realtime'),
        'workflow_integration': ('Workflow<br/>Integration', 'workflow'),
        'output_licensing': ('Output<br/>Licensing', 'licensing'),
        'community_support': ('Community<br/>Support', 'community'),
        'conditioning_inputs': ('Conditioning<br/>Inputs', 'conditioning'),
        'time_varying_control': ('Time-Varying<br/>Control', 'timevarying'),
        'feature_disentanglement': ('Feature<br/>Disentanglement', 'disentanglement'),
        'control_parameters': ('Control<br/>Parameters', 'parameters')
    }
    
    # Generate criterion headers for all dimensions
    for dimension in ['adaptability', 'usability', 'controllability']:
        if dimension == 'adaptability':
            criteria = ['hardware_requirements', 'dataset_size', 'adaptation_pathways', 'technical_barriers', 'model_redistribution']
        elif dimension == 'usability':
            criteria = ['interface_availability', 'access_restrictions', 'realtime_capabilities', 'workflow_integration', 'output_licensing', 'community_support']
        else:
            criteria = ['conditioning_inputs', 'time_varying_control', 'feature_disentanglement', 'control_parameters']
        
        for criterion in criteria:
            display_name, criterion_id = criterion_info[criterion]
            criterion_key = f'{dimension}.{criterion}'
            has_tags = criterion_key in tags_by_criterion and len(tags_by_criterion[criterion_key]) > 0
            
            html_table += '<th><div class="criterion-header-wrapper">'
            html_table += '<span>' + display_name + '</span>'
            
            # Add tags if available
            if has_tags:
                # Sort tags by length (shortest first) for optimal packing
                sorted_tags = sorted(tags_by_criterion[criterion_key], key=len)
                html_table += '<div class="criterion-tags" data-criterion="' + criterion_id + '">'
                
                # Add all tags (JavaScript will handle visibility based on row calculations)
                for tag in sorted_tags:
                    html_table += f'<span class="criterion-tag" data-tag="{tag}" data-criterion="{criterion_id}">{tag}</span>'
                
                # Add expand button placeholder (JavaScript will show/hide and update count)
                html_table += '<span class="expand-tags-btn" data-criterion="' + criterion_id + '">+0</span>'
                
                html_table += '</div>'
            
            html_table += '</div></th>'
    
    html_table += '</tr>\n'
    html_table += '</thead>\n'
    html_table += '<tbody>\n'
    
    # Generate table rows
    for p in projects:
        affiliation = df.loc[p, "project.affiliation"] if "project.affiliation" in df.columns else ""
        project_link = df.loc[p, "project.link"] if "project.link" in df.columns else ""
        
        row_tags = []
        for dimension in ['adaptability', 'usability', 'controllability']:
            if dimension == 'adaptability':
                criteria = ['hardware_requirements', 'dataset_size', 'adaptation_pathways', 'technical_barriers', 'model_redistribution']
            elif dimension == 'usability':
                criteria = ['interface_availability', 'access_restrictions', 'realtime_capabilities', 'workflow_integration', 'output_licensing', 'community_support']
            else:
                criteria = ['conditioning_inputs', 'time_varying_control', 'feature_disentanglement', 'control_parameters']
            
            for criterion in criteria:
                criterion_id = criterion_info[criterion][1]
                
                # Collect explicit tags from YAML
                tags_col = f'{dimension}.{criterion}.tags'
                if tags_col in df.columns:
                    tags_val = df.loc[p, tags_col]
                    if tags_val and isinstance(tags_val, str):
                        tags_list = [t.strip() for t in tags_val.split(',')]
                        # Add criterion-specific tags as criterion_id:tag_name
                        row_tags.extend([f'{criterion_id}:{tag}' for tag in tags_list])
                
                # Add synthetic tags based on value level
                if criterion in synthetic_tags:
                    value_col = f'{dimension}.{criterion}.value'
                    if value_col in df.columns:
                        value = df.loc[p, value_col]
                        if value in synthetic_tags[criterion]:
                            synthetic_tag_list = synthetic_tags[criterion][value]
                            if synthetic_tag_list:
                                row_tags.extend([f'{criterion_id}:{tag}' for tag in synthetic_tag_list])
        
        # Collect applications for this project
        row_applications = []
        if 'project.applications' in df.columns:
            apps = df.loc[p, 'project.applications']
            if apps and isinstance(apps, str):
                row_applications = [a.strip() for a in apps.split(',')]
        
        r1_html = f"""<tr class="row-a" data-name="{p}" data-affiliation="{affiliation}" data-adaptability="{int(df.loc[p, 'adaptability_score'])}" data-usability="{int(df.loc[p, 'usability_score'])}" data-controllability="{int(df.loc[p, 'controllability_score'])}" data-overall="{int(df.loc[p, 'overall_score'])}" data-tags="{','.join(row_tags)}" data-applications="{','.join(row_applications)}">"""
        
        # Model name cell with affiliation below
        r1_html += '<td class="name-cell">'
        if project_link:
            r1_html += f'<div class="model-name"><a href="{project_link}" target="_blank">{p}</a></div>'
        else:
            r1_html += f'<div class="model-name">{p}</div>'
        if affiliation:
            r1_html += f'<div class="affiliation">{affiliation}</div>'
        r1_html += '</td>'
        
        # Adaptability cells
        for criterion in ['hardware_requirements', 'dataset_size', 'adaptation_pathways', 'technical_barriers', 'model_redistribution']:
            val = df.loc[p, f'adaptability.{criterion}.value']
            notes = df.loc[p, f'adaptability.{criterion}.notes']
            css_class = val if val else "empty"
            symbol = "✔︎" if val == "high" else ("~" if val == "partial" else ("✘" if val == "low" else ""))
            r1_html += f'<td class="{css_class} data-cell" title="{notes}">{symbol}</td>'
        
        # Usability cells
        for criterion in ['interface_availability', 'access_restrictions', 'realtime_capabilities', 'workflow_integration', 'output_licensing', 'community_support']:
            val = df.loc[p, f'usability.{criterion}.value']
            notes = df.loc[p, f'usability.{criterion}.notes']
            css_class = val if val else "empty"
            symbol = "✔︎" if val == "high" else ("~" if val == "partial" else ("✘" if val == "low" else ""))
            r1_html += f'<td class="{css_class} data-cell" title="{notes}">{symbol}</td>'
        
        # Controllability cells
        for criterion in ['conditioning_inputs', 'time_varying_control', 'feature_disentanglement', 'control_parameters']:
            val = df.loc[p, f'controllability.{criterion}.value']
            notes = df.loc[p, f'controllability.{criterion}.notes']
            css_class = val if val else "empty"
            symbol = "✔︎" if val == "high" else ("~" if val == "partial" else ("✘" if val == "low" else ""))
            r1_html += f'<td class="{css_class} data-cell" title="{notes}">{symbol}</td>'
        
        r1_html += "</tr>\n"
        html_table += r1_html
    
    html_table += '</tbody>\n'
    html_table += '</table>\n'
    
    # Generate applications tags HTML section
    applications_html = '<div class="applications-section">\n'
    applications_html += '<h3 class="applications-title">Musical Applications</h3>\n'
    applications_html += '<div class="applications-tags-container">\n'
    for app in sorted_applications:
        applications_html += f'<span class="application-tag" data-application="{app}">{app}</span>\n'
    applications_html += '</div>\n'
    applications_html += '</div>\n'
    
    return html_table, applications_html


def create_index(table, applications_html):
    with open("./docs/template.html", "r", encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    
    # Insert applications tags into the applications wrapper
    if applications_html:
        target_element = soup.find(id="applications-wrapper")
        if target_element:
            apps_soup = BeautifulSoup(applications_html, 'html.parser')
            target_element.append(apps_soup)
    
    # Insert table into the table container
    target_element = soup.find(id="included-table")
    target_element.append(BeautifulSoup(table, 'html.parser'))
    
    utc_datetime = datetime.datetime.utcnow()
    build_message = utc_datetime.strftime("Table last built on %Y-%m-%d at %H:%M UTC")
    target_footer = soup.find(id="build-time")
    if target_footer:
        target_footer.string = build_message
    
    with open("./docs/index.html", 'w', encoding='utf-8') as f:
        f.write(str(soup))


# Main execution
path = r'./projects'
all_files = glob.glob(path + "/*.yaml")
# Exclude templates
all_files = [f for f in all_files if '_template' not in f]

print('Processing files:', all_files)

df = create_dataframe(all_files)
df = calculate_scores(df)

# Sort by overall score (descending)
df = df.sort_values(by="overall_score", ascending=False)

table, tags_html = write_html(df)
create_index(table, tags_html)

# Save CSV
df.to_csv("./docs/df.csv", index=False)

print("✓ Table generated successfully!")
