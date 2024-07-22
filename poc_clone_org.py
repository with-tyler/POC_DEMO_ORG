import configparser
import requests
import json

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')
config_vars = {key: config['DEFAULT'][key] for key in config['DEFAULT']}

# Define headers for API requests
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Token {config_vars["api_token"]}'
}

# Function to clone an organization
def clone_organization(source_org_id, new_org_name):
    url = f'{config_vars["base_url"]}/orgs/{source_org_id}/clone'
    payload = {'name': new_org_name}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json()['id']
    else:
        raise Exception(f"Failed to clone organization: {response.text}")

# Function to create a new site
def create_site(org_id, site_name, site_address, country_code):
    url = f'{config_vars["base_url"]}/orgs/{org_id}/sites'
    payload = {'name': site_name, 'address': site_address, 'country_code': country_code}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json()['id']
    else:
        raise Exception(f"Failed to create site: {response.text}")

# Function to copy site settings including variables
def copy_site_settings(source_site_id, target_site_id):
    url = f'{config_vars["base_url"]}/sites/{source_site_id}/setting'
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to get source site settings: {response.text}")
    site_settings = response.json()
    
    url = f'{config_vars["base_url"]}/sites/{target_site_id}/setting'
    response = requests.put(url, headers=headers, data=json.dumps(site_settings))
    if response.status_code != 200:
        raise Exception(f"Failed to update target site settings: {response.text}")

# Function to fetch template IDs from the new organization
def fetch_template_ids(org_id, source_organization_id):
    template_ids = {}
    endpoints = {
        'switch_template_id': f'{config_vars["base_url"]}/orgs/{org_id}/networktemplates',
        'wan_edge_template_id': f'{config_vars["base_url"]}/orgs/{org_id}/gatewaytemplates',
        'wlan_template_id': f'{config_vars["base_url"]}/orgs/{org_id}/templates',
        'service_policies': f'{config_vars["base_url"]}/orgs/{source_organization_id}/servicepolicies'
    }
    
    for key, url in endpoints.items():
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            if key == 'service_policies':
                template_ids[key] = response.json()
            else:
                template_ids[key] = response.json()[0]['id']  # Assuming the first template is the desired one
        else:
            raise Exception(f"Failed to fetch {key}: {response.text}")
    
    return template_ids

# Function to assign templates to a site
def assign_templates(org_id, site_id, template_ids):
    assignments = {
        'switch_template_id': {"networktemplate_id": template_ids.get('switch_template_id')},
        'wlan_template_id': {"applies": {"org_id": org_id}},
        'wan_edge_template_id': {"gatewaytemplate_id": template_ids.get('wan_edge_template_id')}
    }
    
    for key, payload in assignments.items():
        if key in template_ids:
            url = f'{config_vars["base_url"]}/sites/{site_id}' if key != 'wlan_template_id' else f'{config_vars["base_url"]}/orgs/{org_id}/templates/{template_ids[key]}'
            response = requests.put(url, headers=headers, data=json.dumps(payload))
            if response.status_code != 200:
                raise Exception(f"Failed to assign {key}: {response.text}")
            print(f"{key.replace('_', ' ').title()} assigned successfully.")
    
    if 'service_policies' in template_ids:
        new_template_policies = []
        url = f'{config_vars["base_url"]}/orgs/{org_id}/servicepolicies'
        for policy in template_ids['service_policies']:
            response = requests.post(url, headers=headers, data=json.dumps(policy))
            if response.status_code == 200:
                pol_id = response.json()["id"]
                service_policy = {
                    'servicepolicy_id': pol_id,
                    'path_preference': "INTERNAL" if response.json()['name'] == "GUEST_BLOCK_INTERNAL" else "WAN1"
                }
                new_template_policies.append(service_policy)
            else:
                raise Exception(f"Failed to assign policy template: {response.text}")
        
        gw_url = f'{config_vars["base_url"]}/orgs/{org_id}/gatewaytemplates/{template_ids["wan_edge_template_id"]}'
        response = requests.put(gw_url, headers=headers, data=json.dumps({"service_policies": new_template_policies}))
        if response.status_code != 200:
            raise Exception(f"Failed to assign policy template to WAN edge: {response.text}")
        print("Service Policies assigned successfully.")

# Function to invite super users to the new organization
def invite_super_users(org_id, user_details):
    url = f'{config_vars["base_url"]}/orgs/{org_id}/invites'
    for detail in user_details:
        email, first_name, last_name = detail.split(':')
        payload = {
            'email': email.strip(),
            'first_name': first_name.strip(),
            'last_name': last_name.strip(),
            'hours': 24,
            'privileges': [{'scope': 'org', 'role': 'admin'}]
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            raise Exception(f"Failed to invite superuser {email}: {response.text}")

# Main execution
def main():
    try:
        new_org_id = clone_organization(config_vars["source_organization_id"], config_vars["new_organization_name"])
        print(f"New organization cloned with ID: {new_org_id}")
        
        new_site_id = create_site(new_org_id, config_vars["site_name"], config_vars["site_address"], config_vars["country_code"])
        print(f"New site created with ID: {new_site_id}")
        
        copy_site_settings(config_vars["source_site_id"], new_site_id)
        print("Site settings copied successfully.")
        
        template_ids = fetch_template_ids(new_org_id, config_vars["source_organization_id"])
        print("Template IDs fetched successfully.")
        
        assign_templates(new_org_id, new_site_id, template_ids)
        print("Templates assigned successfully to the new site.")
        
        invite_super_users(new_org_id, config_vars["new_superuser_details"].split(','))
        print("Super users invited successfully to the new organization.")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()