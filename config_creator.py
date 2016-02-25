#!/usr/bin/python3

import getopt
import os
import sys

sip_conf_path = 'sip.conf'
output_path = 'out/'
template_path = ''


def find_secret(peer, sip_conf_path):
    secret = ''
    found = False
    sip_conf = read_config(sip_conf_path)
    template = ''

    def find_secret_in_template():
        template_secret_found = False
        for line in sip_conf:
            if not template_secret_found:
                if '[' + template + ']' in line:
                    template_secret_found = True
            else:
                if line[:6] == 'secret':
                    return line[7:]
                if line[1] == '[':
                    return ''

    for line in sip_conf:
        if not found:
            if len(line) >= len(peer) + 2:
                if '[' + peer + ']' in line:
                    found = True
                    if len(line) > len(peer) + 2:
                        if '(' in line and ')' in line:
                            temp = line.split('(')
                            temp = temp[1].split(')')
                            template = temp[0]
        else:
            if line[:6] == 'secret':
                secret = line[7:]
                break
            if '[' in line:
                if template != '':
                    secret = find_secret_in_template()
                    break
                else:
                    break
    return secret


def replace_value_in_quotas(string_with_quotas, new_value):
    return string_with_quotas[:string_with_quotas.find('"') + 1] + \
           new_value + string_with_quotas[string_with_quotas.find('"', string_with_quotas.find('"') + 1):]


def find_last_port_line_index(config_path, port):
    lines = read_config(config_path)

    def find(lines, port):
        first_port_line = 0
        last_port_line = 0
        first_port_line_found = False
        line_found = False
        for index, line in enumerate(lines):
            if not first_port_line_found and '[' in line:
                if line[0] == '#':
                    pass
                else:
                    first_port_line = index - 1
                    first_port_line_found = True
            if '[' + port + ']' in line:
                line_found = True
                last_port_line = index
        if line_found:
            return last_port_line
        else:
            if port == '0':
                if first_port_line_found:
                    return first_port_line
                else:
                    return len(lines) - 1
            return find(lines, str(int(port) - 1))

    return find(lines, port)


def find_port_by_peer(config_path, peer):
    lines = read_config(config_path)
    for line in lines:
        if 'User_ID' in line:
            line = line.split('"')
            if line[1] == peer:
                temp = ""
                for ch in line[0]:
                    if ch.isdigit():
                        temp += ch
                return temp
    return '-1'


def read_config(path):
    with open(path, encoding='utf-8') as configfile:
        config = configfile.read().splitlines()
    return config


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
                if len(line) != 2:
                    print('Error! Wrong parameter file format. Nothing changed.')
                    usage()
                    return
                elif not line[1].isdigit():
                    print('Error! Wrong parameter file format. Nothing changed.')
                    usage()
                    return
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
    if os.path.exists(output_path + gw_type + '.' + mac + '.txt'):
        print('Error! File {} is exist. Configuration does not created.'.format(
            output_path + gw_type + '.' + mac + '.txt'))
        return
    with open(gw_type + '-template-config.txt') as configfile:
        conf_template = configfile.read()
    with open(output_path + gw_type + '.' + mac + '.txt', 'w') as config:
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
                if len(line) != 2:
                    print('Error! Wrong parameter file format. Nothing changed.')
                    usage()
                    return
                elif not line[1].isdigit():
                    print('Error! Wrong parameter file format. Nothing changed.')
                    usage()
                    return
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
    print('Usage: {} --action [addport | change | create | enable | disable] '.format(sys.argv[0]), end='')
    print('''-t gwType -m mac_address [[-p port] [-P peer] | [--file file]]
\nFile format:
peer1:port1
peer2:port2
...
peerN:portN'''.format(sys.argv[0]))


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
        if options['--action'] == 'add':
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
            if '-p' in options.keys():
                enable_disable_port(config_path, options['-p'], True)
            elif '-P' in options.keys():
                enable_disable_port(config_path, find_port_by_peer(config_path, options['-P']), True)
            else:
                raise KeyError('Key -p or -P not found.')
        elif options['--action'] == 'disable':
            if '-p' in options.keys():
                enable_disable_port(config_path, options['-p'], False)
            elif '-P' in options.keys():
                enable_disable_port(config_path, find_port_by_peer(config_path, options['-P']), False)
            else:
                raise KeyError('Key -p or -P not found.')
    except KeyError as err:
        print('Argument {} is missing'.format(err))
        usage()
    except FileNotFoundError as err:
        print(err)


if __name__ == "__main__":
    # main(sys.argv[1:])
    # For tests:
    params = '--action add -t spa8000 -m aabbccddeeff --file 124.txt'
    main(params.split())
