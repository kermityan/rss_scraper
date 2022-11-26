# You shouldn't change  name of function or their arguments
# but you can change content of the initial functions.
import sys
from argparse import ArgumentParser
from typing import List, Optional, Sequence
import html

import requests


class UnhandledException(Exception):
    pass


def rss_parser(
        xml: str,
        limit: Optional[int] = None,
        json: bool = False,
) -> List[str]:
    """
    RSS parser.

    Args:
        xml: XML document as a string.
        limit: Number of the news to return. if None, returns all news.
        json: If True, format output as JSON.

    Returns:
        List of strings.
        Which then can be printed to stdout or written to file as a separate lines.

    Examples:
        >>> xml = '<rss><channel><title>Some RSS Channel</title><link>https://some.rss.com</link><description>Some RSS Channel</description></channel></rss>'
        >>> rss_parser(xml)
        ["Feed: Some RSS Channel",
        "Link: https://some.rss.com"]
        >>> print("\\n".join(rss_parser(xmls)))
        Feed: Some RSS Channel
        Link: https://some.rss.com
    """
    # Your code goes here
    tags = {
        'channel': {
            '<channel>': ('', ''),
            '<title>': ('Feed', '"title"'),
            '<link>': ('Link', '"link"'),
            '<description>': ('Description', '"description"'),
            '<category>': ('Categories', '"category"'),
            '<language>': ('Language', '"language"'),
            '<lastBuildDate>': ('Last Build Date', '"lastBuildDate"'),
            '<managinEditor>': ('Editor', '"managinEditor"'),
            '<pubDate>': ('Publish Date', '"pubDate"'),
            '<item>': ('', '"items"')
        },

        'item': {
            '<title>': ('Title', '"title"'),
            '<author>': ('Author', '"author"'),
            '<pubDate>': ('Date', '"pubDate"'),
            '<link>': ('Link', '"link"'),
            '<category>': ('Categories', '"category"'),
            '<description>': ('\n', '"description"')
        }
    }

    def parse_item(cur_item: str, tag: str):
        """
        Parses one item in RSS feed. Returns substring between <tag> and </tag>.
        :param cur_item: String between <item> and </item> tags
        :param tag: Tag to find in the item
        :return: String between <tag> and </tag>
        """
        element_str = ""
        tag_len = len(tag)
        close_tag = '</' + tag[1:]
        b_ind = cur_item.find(tag) + tag_len
        e_ind = cur_item.find(close_tag)
        if b_ind != -1 and e_ind != -1:
            element_str = cur_item[b_ind:e_ind]
        return html.unescape(element_str)

    def find_categories(search_str):
        beg_ind = search_str.find('<category>') + 10
        end_ind = search_str.find('</category>')
        result = ""
        while beg_ind != -1 and end_ind != -1:
            category = search_str[beg_ind:end_ind]
            result += category + ", "
            search_str = search_str[end_ind + 11:]
            beg_ind = search_str.find('<category>') + 10
            end_ind = search_str.find('</category>')
        result = result[:-2]
        #print(result)
        return result

    def tags_list(search_str: str, scope: str, jsn: bool) -> List[str]:
        result = []
        nonlocal level
        for tag in tags[scope].keys():
            if tag == '<category>':
                next_str = find_categories(search_str)

            else:
                next_str = parse_item(search_str, tag)

            if next_str:
                if jsn:
                    intend = ' ' * level * 2
                    result.append(f'{intend}{tags[scope][tag][1]}: "{next_str.strip()}",')
                else:
                    if tag == '<description>' and scope == 'item':
                        result.append('')
                        result.append(next_str.strip())
                    else:
                        result.append(f'{tags[scope][tag][0]}: {next_str.strip()}')

        if not json:
            result.append('')
        elif scope == 'item':
            result[-1] = result[-1][:-1]
        return result

    channel_list = []
    items_list = []
    parsing_str = xml
    limiting = True
    item_count = 0
    if limit and limit < 0:
        limit = None
    if limit or limit == 0:
        limiting = item_count < limit

    level = 0
    beg_ind = parsing_str.find('<channel>') + 9
    end_ind = parsing_str.find('<item>') if parsing_str.find('<item>') != -1 else parsing_str.find('</channel>')
    header = parsing_str[beg_ind:end_ind]
    if header and json:
        channel_list.append('{')
        level += 1
    #print(header,'\n',tags_list(header, 'channel', json), '\n')

    channel_list.extend(tags_list(header, 'channel', json))

    beg_ind = parsing_str.find('<item>') + 6
    end_ind = parsing_str.find('</item>')
    if end_ind != -1:
        if json:
            intend = ' ' * level * 2
            items_list.append(f'{intend}"items": [')
            level += 1


        while beg_ind != -1 and end_ind != -1 and limiting:
            #print(item_count, limit, limiting)
            item = parsing_str[beg_ind:end_ind]
            item_count += 1
            if json:
                intend = ' ' * level * 2
                items_list.append(intend + '{')
                level += 1
            items_list.extend(tags_list(item, 'item', json))
            if json:
                level -= 1
                intend = ' ' * level * 2
                items_list.append(intend + '},')

            parsing_str = parsing_str[end_ind + 7:]
            beg_ind = parsing_str.find('<item>') + 6
            end_ind = parsing_str.find('</item>')
            if limit or limit == 0:
                limiting = item_count < limit
        if json:
            items_list[-1] = items_list[-1][:-1]
            level -= 1
            intend = ' ' * level * 2
            items_list.append(intend + ']')
    if json:
        level -= 1
        intend = ' ' * level * 2
        items_list.append(intend + '}')
    #print(channel_list, items_list)
    return channel_list + items_list


def main(argv: Optional[Sequence] = None):
    """
    The main function of your task.
    """

    parser = ArgumentParser(
        prog="rss_reader",
        description="Pure Python command-line RSS reader.",
    )
    parser.add_argument("source", help="RSS URL", type=str, nargs="?")
    parser.add_argument(
        "--json", help="Print result as JSON in stdout", action="store_true"
    )
    parser.add_argument(
        "--limit", help="Limit news topics if this parameter provided", type=int
    )

    args = parser.parse_args(argv)
    xml = requests.get(args.source).text

    try:
        print("\n".join(rss_parser(xml, args.limit, args.json)))
        return 0
    except Exception as e:
        raise UnhandledException(e)


if __name__ == "__main__":
    main()
