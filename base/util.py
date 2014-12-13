from collections import namedtuple

ArticleProto = namedtuple(
    'ArticleProto',
    ['title', 'summary', 'url', 'timestamp', 'origin', 'image_url', 'source_id', 'origin_img', 'origin_display_name', 'time_unkown'],
)