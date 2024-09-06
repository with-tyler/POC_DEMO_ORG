# Baseline Proof of Concept (POC) Site Automation

This Python program is designed to automate the creation of a cloned version of a Baseline Proof of Concept (POC) organization using the Mist API. The program provides a robust deployment model that ensures all templates and variables are cloned, including organizational-level variables, which are not typically cloned when using the Mist dashboard. Furthermore, this can be the framework for automating other functions of the Mist Dashboard.

## Key Features and Functions

1. **Organization Cloning**:
   - The program clones an existing organization, replicating all organization-wide settings from the source organization to the new organization. This includes security policies, switch templates, WAN Edge templates, and WLAN templates.

2. **Site Creation and Configuration**:
   - A new site is created within the cloned organization. The program then copies all settings from a specified source site to the newly created site. This includes site-specific variables and configurations such as Auto Firmware Upgrade, Location Services settings, RF Templates, Webhooks, and Rogue/Honeypot AP configurations.

3. **Template Assignment**:
   - The program fetches template IDs from the new organization and assigns them to the new site. This includes switch templates, WAN Edge templates, WLAN templates, and policy templates. The templates are assigned at the site level, ensuring that all necessary configurations are applied to the new site.
   - The WLAN template includes a single SSID on the CORP network and a single Guest SSID on the GUEST network.

4. **Application Policies**:
   - Application policies from the source organization are copied and applied to the new WAN Edge template. This ensures that all security and application policies are consistently enforced in the new organization.

5. **Super User Invitations**:
   - The program allows for the automatic invitation of new super users to the new organization. User details, including email addresses, first names, and last names, are specified in the configuration file. The program sends invitations to these users, granting them superuser roles in the new organization.

6. **Configuration File**:
   - The program uses a configuration file (`config.ini`) to store necessary variables such as API tokens, organization IDs, site names, and superuser details. This allows for easy customization and reuse of the program for different organizations and sites.

## Technical Details

- **API Integration**:
  - The program leverages the Mist RESTful API to perform various operations, including cloning organizations, site creation, copying site settings, fetching and assigning templates, and inviting super users. The API uses HTTPS requests and JSON format for data exchange, ensuring secure and efficient communication with the Mist cloud.

- **Error Handling**:
  - The program includes error handling mechanisms to ensure that any issues encountered during the execution are properly reported. This includes checking the status codes of API responses and raising exceptions for any failed operations.

- **Automation and Scalability**:
  - By automating the process of cloning organizations and configuring sites, the program significantly reduces the time and effort required for manual setup. This makes it ideal for large-scale deployments and scenarios where consistent configuration across multiple sites is required.

## Usage

1. **Requirements**:
   - Ensure that you have installed the packages found in requirements.txt.
   - Verify you have a valid API token to the MSP instance for **your** BASELINE_POC_ORG in Mist that has the baseline ORG for cloning with the correct access.

2. **Configuration**:
   - Update the `example_config.ini` file with the necessary variables, including the API token, source organization ID, new organization name, new site name, and superuser details. All required information in the configuration file are marked in the "# REQUIRED INFORMATION" section.
   - When adding Super Users to an ORG, they will only be assigned to the organization with full access to the entire organization. An invite will be sent to them immediately and they will have 24 hours to accept their invite; otherwise, you will have to resend the invitation.
     - You must utilize the format prescribed in the `example_config.ini`:
     - For example: {email}:FirstName:LastName,{email}:FirstName:LastName
   - Save the newly edited `example_config.ini` in the same directory as the python program `baseline_org_clone.py` as `config.ini`.
         - This will ensure that your config.ini does change on updates and updates can be merged as needed.
   - Do not make edits to the "# DO NOT CHANGE # section once you have it configured as applicable.

3. **Execution**:
   - Run the program to clone the organization, create the new site, copy settings, assign templates, copy application policies, and invite super users.

4. **Verification**:
   - Verify that the new organization and site have been created and configured correctly, with all templates and policies applied as expected.

5. **Switch Configuration**:
   - Assign the Switch Template to the desired switch via the role function at switch level to incorporate the port rules depending on the device, BASELINE_[12|24|48], based on the port counts.
   - Each port rule in the template uses the first two ports, ge-0/0/[0-1], for the AP Uplink and the last copper port for the Uplink.

6. **WAN Edge Configuration**:
   - The WAN Edge template utilizes port ge-0/0/0 for its WAN1 link only.
   - Port ge-0/0/1 is utilized as a trunk with Native VLAN ID for downlink to the switch.

7. **Adopt Devices into Inventory for Deployment**:
   - Once inventory is adopted, all configurations will be applied as devices are assigned to the site created in the new ORG.

Note: Review all configurations and make modifications to the any piece of the configuration. If a simple VLAN or network change is required, please use the site variables section to do so. Some configurations in the WAN Edge template cannot use site variables, ensure those settings match accordingly.

### Current Site Variables

``` json
{
   "CAMERA": "50",
   "CORP": "20",
   "DNS1": "1.1.1.1",
   "DNS8": "8.8.8.8",
   "DNS9": "9.9.9.9",
   "GUEST": "40",
   "IOT": "70",
   "MGMT": "10",
   "NETWORK": "10.10.",
   "NTP1": "0.pool.ntp.org",
   "NTP2": "1.pool.ntp.org",
   "STORAGE": "30",
   "VOIP": "60"
}
```
