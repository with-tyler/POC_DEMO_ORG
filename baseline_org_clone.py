import configparser
import requests
import json

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Extract configuration variables
api_token = config['DEFAULT']['api_token']
base_url = config['DEFAULT']['base_url']
source_organization_id = config['DEFAULT']['source_organization_id']
new_organization_name = config['DEFAULT']['new_organization_name']
source_site_id = config['DEFAULT']['source_site_id']
site_name = config['DEFAULT']['site_name']
site_address = config['DEFAULT']['site_address']
country_code = config['DEFAULT']['country_code']
new_superuser_details = config['DEFAULT']['new_superuser_details'].split(',')

# Define headers for API requests
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Token {api_token}'
}

# Function to clone an organization
def clone_organization(source_org_id, new_org_name):
    url = f'{base_url}/orgs/{source_org_id}/clone'
    payload = {'name': new_org_name}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json()['id']
    else:
        raise Exception(f"Failed to clone organization: {response.text}")

# Function to create a new site
def create_site(org_id, site_name, site_address, country_code):
    url = f'{base_url}/orgs/{org_id}/sites'
    payload = {'name': site_name, 'address': site_address, 'country_code': country_code}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json()['id']
    else:
        raise Exception(f"Failed to create site: {response.text}")

# Function to copy site settings including variables
def copy_site_settings(source_site_id, target_site_id):
    # Get settings from the source site
    url = f'{base_url}/sites/{source_site_id}/setting'
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to get source site settings: {response.text}")
    site_settings = response.json()

    # Update the target site with the copied settings
    url = f'{base_url}/sites/{target_site_id}/setting'
    response = requests.put(url, headers=headers, data=json.dumps(site_settings))
    if response.status_code != 200:
        raise Exception(f"Failed to update target site settings: {response.text}")

# Function to fetch template IDs from the new organization
def fetch_template_ids(org_id, source_organization_id):
    template_ids = {}

    # Fetch switch templates
    url = f'{base_url}/orgs/{org_id}/networktemplates'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        template_ids['switch_template_id'] = response.json()[0]['id']  # Assuming the first template is the desired one

    # Fetch WAN edge templates
    url = f'{base_url}/orgs/{org_id}/gatewaytemplates'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        template_ids['wan_edge_template_id'] = response.json()[0]['id']  # Assuming the first template is the desired one

    # Fetch WLAN templates
    url = f'{base_url}/orgs/{org_id}/templates'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        template_ids['wlan_template_id'] = response.json()[0]['id']  # Assuming the first template is the desired one

    # Fetch service policy templates
    url = f'{base_url}/orgs/{source_organization_id}/servicepolicies'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        template_ids['service_policies'] = response.json()

    return template_ids

# Function to assign templates to a site
def assign_templates(org_id, site_id, template_ids):
    # Assign switch template
    if 'switch_template_id' in template_ids:
        print("Assigning switch template")
        print(f'Switch template ID: {template_ids["switch_template_id"]}')
        url = f'{base_url}/sites/{site_id}'
        payload = {"networktemplate_id": f"{template_ids["switch_template_id"]}"}
        response = requests.put(url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            raise Exception(f"Failed to assign switch template: {response.text}")
        print("Completed Switch Template Assign")

    # Assign WLAN template
    if 'wlan_template_id' in template_ids:
        print("Assigning WLAN template")
        url = f'{base_url}/orgs/{org_id}/templates/{template_ids["wlan_template_id"]}'
        payload = {"applies":{"org_id":f"{org_id}"}}
        response = requests.put(url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            raise Exception(f"Failed to assign WLAN template: {response.text}")
        print("WLAN Template Complete")

    # Assign service policy templates
    if 'service_policies' in template_ids:
        new_template_policies = []
        print("Assigning Service Policies to ORG")
        url = f'{base_url}/orgs/{org_id}/servicepolicies'
        policies = [policy for policy in template_ids["service_policies"]]
        for payload in policies:
            service_policy = {}
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            pol_id = response.json()["id"]
            if response.status_code != 200:
                raise Exception(f"Failed to assign policy template: {response.text}")
            if response.json()['name'] == "GUEST_BLOCK_INTERNAL":
                service_policy = dict(servicepolicy_id = pol_id, path_preference = "INTERNAL")
            else:
                service_policy = dict(servicepolicy_id = pol_id, path_preference = "WAN1")
            new_template_policies.append(service_policy)
        # Assign Service policies WAN Edge Template
        gw_url = f'{base_url}/orgs/{org_id}/gatewaytemplates/{template_ids["wan_edge_template_id"]}'
        fdata = {"service_policies": new_template_policies}
        # print("Data:", fdata)
        response = requests.put(gw_url, headers=headers, data=json.dumps(fdata))
        if response.status_code != 200:
                raise Exception(f"Failed to policy template to WAN edge: {response.text}")
        print("Service Policies Complete")

    # Assign WAN edge template
    if 'wan_edge_template_id' in template_ids:
        print("Assigning WAN Edge template.")
        url = f'{base_url}/sites/{site_id}'
        payload = {"gatewaytemplate_id": f"{template_ids["wan_edge_template_id"]}"}
        response = requests.put(url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            raise Exception(f"Failed to assign WAN edge template: {response.text}")
        print("WAN Edge template complete")

# Function to invite super users to the new organization
def invite_super_users(org_id, user_details):
    url = f'{base_url}/orgs/{org_id}/invites'
    for detail in user_details:
        email, first_name, last_name = detail.split(':')
        payload = {'email': email.strip(),'first_name': first_name.strip(),'last_name': last_name.strip(),'hours': 24, 'privileges': [{'scope': 'org','role': 'admin'}]}
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            raise Exception(f"Failed to invite superuser {email}: {response.text}")

# Main execution
try:
    # Clone the organization
    new_org_id = clone_organization(source_organization_id, new_organization_name)
    print(f"New organization cloned with ID: {new_org_id}")

    # Create new site in the new organization
    new_site_id = create_site(new_org_id, site_name, site_address, country_code)
    print(f"New site created with ID: {new_site_id}")

    # Copy settings from the original site to the new site
    copy_site_settings(source_site_id, new_site_id)
    print("Site settings copied successfully.")

    # Fetch template IDs from the new organization
    template_ids = fetch_template_ids(new_org_id, source_organization_id)
    print("Template IDs fetched successfully.")

    # Assign templates to the new site
    assign_templates(new_org_id, new_site_id, template_ids)
    print("Templates assigned successfully to the new site.")

    # Invite super users to the new organization
    invite_super_users(new_org_id, new_superuser_details)
    print("Super users invited successfully to the new organization.")

except Exception as e:
    print(f"Error: {e}")