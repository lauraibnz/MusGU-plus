# CSV to YAML converter for MusGU+ evaluations
# Converts Notion export to structured YAML files

import csv
import yaml
import os
import copy

# File paths
csv_file_path = './misc/MusGU+ 2cd73fee0f4280859c39dab5b950f451_all.csv'
yaml_template_path = './projects/_template.yaml'
output_yaml_path = './projects/'

initial_comments = """---
####################################################################################################################################
# MusGU+ evaluation
# A Musician-Centered Evaluation Framework for Generative Music AI
####################################################################################################################################

"""

def normalize_value(val):
    """Convert CSV symbols to standard format"""
    if not val or val.strip() == '':
        return ''
    val = val.strip()
    if val == '✓':
        return 'high'
    elif val == '~':
        return 'partial'
    elif val == '✗' or val == '✘':
        return 'low'
    return val

def load_yaml_template(template_path):
    with open(template_path, 'r') as template_file:
        return yaml.safe_load(template_file)

def write_yaml_file(data, output_path, modelname):
    output_file = os.path.join(output_path, modelname + ".yaml")
    
    with open(output_file, 'w', encoding='utf-8') as yaml_file:
        yaml_file.write(initial_comments)
        yaml.dump(data, yaml_file, default_flow_style=False, allow_unicode=True, sort_keys=False)

def csv_to_yaml(csv_path, yaml_template):
    with open(csv_path, 'r', encoding='utf-8-sig') as csv_file:  # utf-8-sig handles BOM
        reader = csv.DictReader(csv_file)
        for row in reader:
            project_data = copy.deepcopy(yaml_template)
            
            # Project metadata
            model_name = row.get('Name', '').strip()
            print(f"Processing: {model_name}")
            project_data['project']['name'] = model_name
            project_data['project']['affiliation'] = row.get('Affiliation(s)', '')
            project_data['project']['architecture'] = row.get('Model Architecture', '')
            project_data['project']['applications'] = row.get('Musical Applications', '')
            project_data['project']['link'] = ''
            project_data['project']['notes'] = ''
            
            # Adaptability
            project_data['adaptability']['hardware_requirements']['value'] = normalize_value(row.get('[A][1] Hardware Requirements', ''))
            project_data['adaptability']['hardware_requirements']['notes'] = row.get('[A][1] Notes', '')
            
            project_data['adaptability']['dataset_size']['value'] = normalize_value(row.get('[A][2] Dataset Size', ''))
            project_data['adaptability']['dataset_size']['notes'] = row.get('[A][2] Notes', '')
            
            project_data['adaptability']['adaptation_pathways']['value'] = normalize_value(row.get('[A][3] Adaptation Pathways', ''))
            project_data['adaptability']['adaptation_pathways']['notes'] = row.get('[A][3] Notes', '')
            project_data['adaptability']['adaptation_pathways']['tags'] = row.get('[A][3] Tags', '')
            
            project_data['adaptability']['technical_barriers']['value'] = normalize_value(row.get('[A][4] Technical Barriers', ''))
            project_data['adaptability']['technical_barriers']['notes'] = row.get('[A][4] Notes', '')
            project_data['adaptability']['technical_barriers']['tags'] = row.get('[A][4] Tags', '')
            
            project_data['adaptability']['model_redistribution']['value'] = normalize_value(row.get('[A][5] Model Redistribution', ''))
            project_data['adaptability']['model_redistribution']['notes'] = row.get('[A][5] Notes', '')
            
            # Controllability
            project_data['controllability']['conditioning_inputs']['value'] = normalize_value(row.get('[C][1] Conditioning Inputs', ''))
            project_data['controllability']['conditioning_inputs']['notes'] = row.get('[C][1] Notes', '')
            project_data['controllability']['conditioning_inputs']['tags'] = row.get('[C][1] Tags', '')
            
            project_data['controllability']['time_varying_control']['value'] = normalize_value(row.get('[C][2] Time-Varying Control', ''))
            project_data['controllability']['time_varying_control']['notes'] = row.get('[C][2] Notes', '')
            
            project_data['controllability']['feature_disentanglement']['value'] = normalize_value(row.get('[C][3] Feature Disentanglement', ''))
            project_data['controllability']['feature_disentanglement']['notes'] = row.get('[C][3] Notes', '')
            project_data['controllability']['feature_disentanglement']['tags'] = row.get('[C][3] Tags', '')
            
            project_data['controllability']['control_parameters']['value'] = normalize_value(row.get('[C][4] Control Parameters', ''))
            project_data['controllability']['control_parameters']['notes'] = row.get('[C][4] Notes', '')
            project_data['controllability']['control_parameters']['tags'] = row.get('[C][4] Tags', '')
            
            # Usability
            project_data['usability']['interface_availability']['value'] = normalize_value(row.get('[U][1] Interface Availability', ''))
            project_data['usability']['interface_availability']['notes'] = row.get('[U][1] Notes', '')
            project_data['usability']['interface_availability']['tags'] = row.get('[U][1] Tags', '')
            
            project_data['usability']['access_restrictions']['value'] = normalize_value(row.get('[U][2] Access Restrictions', ''))
            project_data['usability']['access_restrictions']['notes'] = row.get('[U][2] Notes', '')
            
            project_data['usability']['realtime_capabilities']['value'] = normalize_value(row.get('[U][3] Real-time Capabilities', ''))
            project_data['usability']['realtime_capabilities']['notes'] = row.get('[U][3] Notes', '')
            
            project_data['usability']['workflow_integration']['value'] = normalize_value(row.get('[U][4] Workflow Integration', ''))
            project_data['usability']['workflow_integration']['notes'] = row.get('[U][4] Notes', '')
            project_data['usability']['workflow_integration']['tags'] = row.get('[U][4] Tags', '')
            
            project_data['usability']['output_licensing']['value'] = normalize_value(row.get('[U][5] Output Licensing', ''))
            project_data['usability']['output_licensing']['notes'] = row.get('[U][5] Notes', '')
            
            project_data['usability']['community_support']['value'] = normalize_value(row.get('[U][6] Community Support', ''))
            project_data['usability']['community_support']['notes'] = row.get('[U][6] Notes', '')
            project_data['usability']['community_support']['tags'] = row.get('[U][6] Tags', '')
            
            # Write YAML file
            write_yaml_file(project_data, output_yaml_path, project_data['project']['name'].lower().replace(' ', '-'))
            print(f"YAML file for {project_data['project']['name']} created successfully.")

yaml_template = load_yaml_template(yaml_template_path)
csv_to_yaml(csv_file_path, yaml_template)
