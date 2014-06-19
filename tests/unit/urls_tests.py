from familytree import urls


class WhenAppendingToSimpleUrl:

    def should_insert_slash_when_missing(self):
        assert urls.append('root', 'extension') == 'root/extension'

    def should_not_insert_unnecessary_slash(self):
        assert urls.append('root/', 'extension') == 'root/extension'

    def should_quote_reserved_characters(self):
        for reserved in ';?:@&=+$,':
            expected = 'root/needs%{0:2x}quote'.format(ord(reserved))
            result = urls.append('root', 'needs{0}quote'.format(reserved))
            assert result.lower() == expected.lower()

    def should_not_quote_embedded_path_separators(self):
        assert urls.append('root', 'embedded/path') == 'root/embedded/path'

    def should_not_insert_unnecessary_path_separators(self):
        assert urls.append('root', 'extra/', 'slash') == 'root/extra/slash'
