from netmiko import ConnectHandler
import getpass
import re
import subprocess


def custom_send_command(net_connect, command):
    print(" --- Sending Command: {}".format(command))
    output = net_connect.send_command(command)
    return output


def parse_dict_list(list):
    headers = []  # Header List
    for header in list[0]:  # The headers are always the first lines that the regex captured.
        headers.append(header.strip())
    list.pop(0)  # Pop the headers and continue

    dict_list = []
    for item in list:
        item_counter = 0
        item_dict = {}
        for header in headers:
            item_dict[header] = item[item_counter].strip()
            item_counter += 1
        dict_list.append(item_dict)

    return dict_list


def main():
    # --- Get User Variables ---
    print(" --- User Variables --- ")
    username = input("Username: ")
    password = getpass.getpass()

    # --- Get the Hostnames ---
    print("Enter Hostnames: [Leave blank to continue]")
    hosts = []
    for i in range(100):
        host = input("").strip()
        if host == "":
            break
        else:
            hosts.append(host)

    # --- Establish SSH Connection ---
    print(" --- Establishing Connection(s) --- ")
    for host in hosts:  # Loop through each hosts
        # Prep a CSV File
        with open('{}.csv'.format(host), 'w') as csv:
            device = {
                'device_type': 'cisco_nxos',
                'host': host,
                'username': username,
                'password': password,
            }  # Create a device based on loop
            net_connect = ConnectHandler(**device)  # Establish SSH Connection
            print(net_connect.find_prompt())  # PRINT - SSH Prompt

            # --- Run / Parse Commands ---
            # 1 - Parse OSPF Interfaces
            regex = r'(.........................)(.......)(................)(.......)(.........)(..........)(.+)'
            string = custom_send_command(net_connect, "show ip ospf interface brief | begin Interface | ex down")
            ospf_interfaces = parse_dict_list(re.findall(regex, string))

            # KEYS - Interface, ID, Area, Cost, State, Neighbors, Status
            # Write CSV Header
            csv.write("Interface, ID, Area, Cost, State, Neighbors, Status, LocalIP,"
                      "Neighbor ID, Neighbor Pri, Neighbor State, Neighbor Up Time, Neighbor Address,"
                      "nslookup, Physical Interface,")  # Write keys before loop
            for interface in ospf_interfaces:  # Loop through each OSPF Interface
                # 2 - Parse IP Interface
                string = custom_send_command(net_connect, 'show ip int {}'.format(interface['Interface']))
                regex = r'IP address: (.+?),'
                interface['LocalIP'] = (re.findall(regex, string)[0].strip())

                # Get Neighbor Information
                if int(interface['Neighbors']) > 0:
                    # 3 - Parse OSPF Neighbors
                    string = custom_send_command(net_connect, 'sh ip ospf neighbors {} | begin Neighbor'.format(
                        interface['Interface']))
                    regex = r'(.................)(....)(.................)(.........)(................)(.+)'
                    ospf_neighbors = parse_dict_list(re.findall(regex, string))

                    # KEYS - Neighbor ID, Pri, State, Up Time, Address, Interface
                    for neighbor in ospf_neighbors:

                        # Get the Neighbor nslookup Data
                        print(" --- Local Command: nslookup {}".format(neighbor['Address']))
                        cmd = "nslookup {}".format(neighbor['Address'])
                        regex = r'Name:(.+)'
                        string = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
                        result = re.findall(regex, string)
                        if len(result) > 0:
                            neighbor['nslookup'] = result[0].strip()
                        else:
                            neighbor['nslookup'] = ""

                        if 'Vlan' in interface['Interface']:  # Find the Physical Port
                            # 4 - Parse ARP Table
                            regex = r'(................)(..........)(................)(.+)'
                            string = custom_send_command(net_connect, 'sh ip arp {} vrf all | beg Address'.format(
                                neighbor['Address']))
                            ospf_neighbors_arp = parse_dict_list(re.findall(regex, string))

                            # KEYS - Address, Age, MAC Address, Interface
                            for arp in ospf_neighbors_arp:  # Find the MAC Address for the neighbor
                                # 5 - Parse MAC Table
                                regex = r'(...........)(..................)(..........)(........)(.......)(....)(.+)'
                                string = custom_send_command(net_connect,
                                                             'sh mac address-table address {} | beg VLAN | exclude -'.format(
                                                                 arp['MAC Address']))
                                ospf_neighbors_physical_interface = parse_dict_list(re.findall(regex, string))

                                # KEYS - VLAN/BD, MAC Address, Type, age, Secure, NTFY, Ports/SWID.SSID.LID
                                for physical_interface in ospf_neighbors_physical_interface:  # Find the physical ports
                                    csv.write(
                                        "\n{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14}".format(
                                            interface['Interface'],
                                            interface['ID'],
                                            interface['Area'],
                                            interface['Cost'],
                                            interface['State'],
                                            interface['Neighbors'],
                                            interface['Status'],
                                            interface['LocalIP'],
                                            neighbor['Neighbor ID'],
                                            neighbor['Pri'],
                                            neighbor['State'],
                                            neighbor['Up Time'],
                                            neighbor['Address'],
                                            neighbor['nslookup'],
                                            physical_interface['Ports/SWID.SSID.LID']
                                        ))

                        else:
                            csv.write("\n{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13}".format(
                                interface['Interface'],
                                interface['ID'],
                                interface['Area'],
                                interface['Cost'],
                                interface['State'],
                                interface['Neighbors'],
                                interface['Status'],
                                interface['LocalIP'],
                                neighbor['Neighbor ID'],
                                neighbor['Pri'],
                                neighbor['State'],
                                neighbor['Up Time'],
                                neighbor['Address'],
                                neighbor['nslookup']
                            ))

                else:
                    # Write Values for loop
                    csv.write("\n{0},{1},{2},{3},{4},{5},{6},{7}".format(
                        interface['Interface'],
                        interface['ID'],
                        interface['Area'],
                        interface['Cost'],
                        interface['State'],
                        interface['Neighbors'],
                        interface['Status'],
                        interface['LocalIP']
                    ))


if __name__ == '__main__':
    main()
