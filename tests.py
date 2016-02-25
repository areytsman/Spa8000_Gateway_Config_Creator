import unittest


class MyTests(unittest.TestCase):
    sip_conf_path = 'test/sip.conf'
    template_path = 'test/'
    config_path = 'test/config.txt'
    out_path = 'out/'

    def test_find_port_by_peer(self):
        from config_creator import find_port_by_peer
        self.assertEqual(find_port_by_peer(self.config_path, '2268'), '22')

    def test_find_secret(self):
        from config_creator import find_secret
        self.assertEqual(find_secret('890202', self.sip_conf_path), 'cmp1juf8d5gfg9')
        self.assertEqual(find_secret('8031004', self.sip_conf_path), '2004')

    def test_replace_value_in_quitas(self):
        from config_creator import replace_value_in_quotas
        self.assertEqual(replace_value_in_quotas('string "value" next', 'new_value'), 'string "new_value" next')

    def test_find_last_port_line_index(self):
        from config_creator import find_last_port_line_index
        self.assertEqual(find_last_port_line_index(self.config_path, '5'), 927)
        self.assertEqual(find_last_port_line_index(self.config_path, '3'), 685)
        self.assertEqual(find_last_port_line_index(self.config_path, '11'), 1893)
        self.assertEqual(find_last_port_line_index(self.config_path, '16'), 1893)

    def test_check_port_is_exist(self):
        from config_creator import check_port_is_exist
        self.assertEqual(check_port_is_exist(self.config_path, '22'), True)
        self.assertEqual(check_port_is_exist(self.config_path, '16'), False)

    def test_get_filename_from_type_and_mac(self):
        from config_creator import get_filename_from_type_and_mac
        self.assertEqual(get_filename_from_type_and_mac('anygw01', '112233445566'),
                         self.out_path + 'anygw01.112233445566.txt')

    def test_get_type_and_mac_from_filename(self):
        from config_creator import get_type_and_mac_from_filename
        self.assertEqual(get_type_and_mac_from_filename('anygw01.112233445566.txt'), ['anygw01', '112233445566'])


if __name__ == '__main__':
    unittest.main()
