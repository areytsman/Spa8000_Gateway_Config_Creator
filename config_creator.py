import getopt
import os
import sys

sip_conf_path = 'sip.conf'
output_path = 'out/'
template_path = ''


def find_secret(peer, sip_conf_path):
    secret = ''
    found = False
    with open(sip_conf_path, encoding='utf-8') as sip_conf:
        for line in sip_conf:
            if not found:
                if len(line) >= len(peer) + 2:
                    if line[1:len(peer) + 1] == peer:
                        found = True
            else:
                if line[:6] == 'secret':
                    secret = line[7:-1]
                    break
                if line[1] == '[':
                    break
    return secret


def replace_value_in_quotas(string_with_quotas, new_value):
    return string_with_quotas[:string_with_quotas.find('"') + 1] + \
           new_value + string_with_quotas[string_with_quotas.find('"', string_with_quotas.find('"') + 1):]


def find_last_port_line_index(config_path, port):
    if int(port) < 1:
        return -1
    with open(config_path) as configfile:
        config = configfile.read()
    if config[-1] == '\r':
        lines = config.split('\n\r')
    else:
        lines = config.split('\n')

    def find(lines, port):
        last_port_line = 0
        line_found = False
        for index, line in enumerate(lines):
            if '[' + port + ']' in line:
                line_found = True
                last_port_line = index
        if line_found:
            return last_port_line
        else:
            return find(lines, str(int(port) - 1))

    return find(lines, port)


def read_config(path):
    with open(path) as configfile:
        config = configfile.read()
    if config[-1] == '\r':
        lines = config.split('\n\r')
    else:
        lines = config.split('\n')
    return lines


def check_port_is_exist(config_path, port):
    config = read_config(config_path)
    for line in config:
        if '[' + port + ']' in line:
            return True
    return False


def change_port_config(config_path, peer, port):
    lines = read_config(config_path)
    secret = find_secret(peer, sip_conf_path)
    if secret == '':
        print("Error! Peer {} not found in sip.conf. Nothing changed".format(peer))
        return
    port_found = False
    user_id_found = False
    password_found = False
    first_port_line = 0
    for index, line in enumerate(lines):
        if '[' + port + ']' in line:
            port_found = True
            if first_port_line == 0:
                first_port_line = index
            if 'User_ID' in line:
                user_id_found = True
                lines[index] = replace_value_in_quotas(line, peer)
            if 'Password' in line:
                password_found = True
                lines[index] = replace_value_in_quotas(line, secret)
    if not port_found:
        print("Error! Port {} does not exist! Nothing changed.".format(port))
        return
    if not user_id_found:
        lines.insert(first_port_line + 1, 'User_ID[{}]                                      "{}" ;'.format(port, peer))
    if not password_found:
        lines.insert(first_port_line + 2,
                     'Password[{}]                                     "{}" ;'.format(port, secret))
    with open(config_path, 'w') as configfile:
        configfile.write('\n'.join(lines))


def change_port_config_from_file(config_path, file_path):
    lines = read_config(config_path)
    data = []
    with open(file_path, newline='\n') as data_file:
        data_file_lines = data_file.read().splitlines()
        for line in data_file_lines:
            if line != "":
                line = line.split(':')
                data.append((line[0], line[1]))
    for peer, port in data:
        secret = find_secret(peer, sip_conf_path)
        if secret == '':
            print("Error! Peer {} not found in sip.conf. Port {} not changed".format(peer, port))
            continue
        port_found = False
        user_id_found = False
        password_found = False
        first_port_line = 0
        for index, line in enumerate(lines):
            if '[' + port + ']' in line:
                port_found = True
                if first_port_line == 0:
                    first_port_line = index
                if 'User_ID' in line:
                    user_id_found = True
                    lines[index] = replace_value_in_quotas(line, peer)
                if 'Password' in line:
                    password_found = True
                    lines[index] = replace_value_in_quotas(line, secret)
        if not port_found:
            print("Error! Port {} does not exist! This port does not changed.".format(port))
            continue
        else:
            if not user_id_found:
                lines.insert(first_port_line + 1, 'User_ID[{}]               \
                                       "{}" ;'.format(port, peer))
            if not password_found:
                lines.insert(first_port_line + 2,
                             'Password[{}]                                     "{}" ;'.format(port, secret))
    with open(config_path, 'w') as configfile:
        configfile.write('\n'.join(lines))


def create_config(gw_type, mac):
    with open(gw_type + '-template-config.txt') as configfile:
        conf_template = configfile.read()
    with open(output_path+gw_type+mac + '.txt', 'w') as config:
        config.write(conf_template)


def add_port_config(config_path, peer, port):
    with open(config_path) as configfile:
        config = configfile.read()
        if config[-1] == '\r':
            lines = config.split('\n\r')
        else:
            lines = config.split('\n')
        for line in lines:
            if '[' + port + ']' in line:
                print("Error! Peer with this port already exists! Nothing changed.")
                return
    secret = find_secret(peer, sip_conf_path)
    if secret == '':
        print("Error! Peer {} not found in sip.conf. Nothing changed".format(peer))
        return
    with open(template_path + get_type_and_mac_from_filename(config_path)[0] + '-template-peer.txt') as temp:
        template_config = temp.read()
    template_config = template_config.replace('{@}', port)
    template_config = template_config.replace('{peer}', peer)
    template_config = template_config.replace('{secret}', secret)
    lines.insert(find_last_port_line_index(config_path, str(int(port) - 1)) + 1, template_config)
    with open(config_path, 'w') as configfile:
        configfile.write('\n'.join(lines))


def add_port_config_from_file(config_path, file_path):
    config = read_config(config_path)
    data = []
    with open(file_path, newline='\n') as data_file:
        data_file_lines = data_file.read().splitlines()
        for line in data_file_lines:
            if line != "":
                line = line.split(':')
                data.append((line[0], line[1]))
    with open(template_path + get_type_and_mac_from_filename(config_path)[0] + '-template-peer.txt') as temp:
        template_config = temp.read()
    commit = []
    data = sorted(data, key=lambda item: int(item[1]), reverse=True)
    for peer, port in data:
        if not check_port_is_exist(config_path, port):
            secret = find_secret(peer, sip_conf_path)
            if secret == '':
                print("Error! Peer {} not found in sip.conf. Port {} not changed".format(peer, port))
                continue
            port_config = template_config.replace('{@}', port)
            port_config = port_config.replace('{peer}', peer)
            port_config = port_config.replace('{secret}', secret)
            commit.append((port_config, find_last_port_line_index(config_path, port) + 1))
        else:
            print('Error! Port {} already exist! This port still not changed.'.format(port))
    for text, index in commit:
        config.insert(index, text)
    with open(config_path, 'w') as configfile:
        configfile.write('\n'.join(config))


def enable_disable_port(config_path, port, enable=True):
    with open(config_path) as configfile:
        config = configfile.read()
    if config[-1] == '\r':
        lines = config.split('\n\r')
    else:
        lines = config.split('\n')
    port_found = False
    enable_found = False
    for index, line in enumerate(lines):
        if '[' + port + ']' in line:
            port_found = True
            if 'Line_Enable' in line:
                enable_found = True
                if enable:
                    lines[index] = replace_value_in_quotas(line, 'Yes')
                else:
                    lines[index] = replace_value_in_quotas(line, 'No')
                break
    if not enable_found:
        if port_found:
            print('Error! No "Line_Enabled" parameter found for port ' + port)
        else:
            print("Error! Port does not exist! Nothing changed.")
    with open(config_path, 'w') as configfile:
        configfile.write('\n'.join(lines))


def usage():
    print(
        'Usage: {} --action [addport | change | create | enable | disable] -t gwType -m mac_address [[-p port] [-P peer] | [--file file]]'.format(
            sys.argv[0]))


def get_filename_from_type_and_mac(gwtype, mac):
    return '{}{}.{}.txt'.format(output_path, gwtype, mac)


def get_type_and_mac_from_filename(filename):
    filename = os.path.basename(filename)
    temp = filename.split('.')
    return [temp[-3], temp[-2]]


def main(argv):
    try:
        optlist, args = getopt.getopt(argv, 't:p:P:m:', ['action=', 'file='])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    options = {}
    for option, arg in optlist:
        options[option] = arg
    try:
        config_path = get_filename_from_type_and_mac(options['-t'], options['-m'])
        if options['--action'] == 'addport':
            if '--file' in options.keys():
                add_port_config_from_file(config_path, options['--file'])
            else:
                add_port_config(config_path, options['-P'], options['-p'])
        elif options['--action'] == 'change':
            if '--file' in options.keys():
                change_port_config_from_file(config_path, options['--file'])
            else:
                change_port_config(config_path, options['-P'], options['-p'])
        elif options['--action'] == 'create':
            create_config(options['-t'], options['-m'])
        elif options['--action'] == 'enable':
            enable_disable_port(config_path, options['-P'], True)
        elif options['--action'] == 'disable':
            enable_disable_port(config_path, options['-P'], False)
    except KeyError as err:
        print('Argument {} is missing'.format(err))
        usage()
    except FileNotFoundError as err:
        print(err)


if __name__ == "__main__":
    main(sys.argv[1:])
    # params = '--action=change --file=123.txt -t spa8000 -m aabbccddee00'
    # main(params.split())
