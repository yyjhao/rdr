from base.database.session import db_session
from base.database.models import Origin, Url


def get_or_create_origin(orig_id):
    origin = db_session.query(Origin).filter_by(identifier=orig_id).first()
    if not origin:
        origin = Origin()
        origin.identifier = orig_id
        db_session.add(origin)
    return origin


def get_or_create_url(url):
    url_row = db_session.query(Url).filter_by(url=url).first()
    if not url_row:
        url_row = Url()
        url_row.url = url
        db_session.add(url_row)
    return url_row
