
import base64
import datetime
import io
import re
import requests
import PyPDF2
import json

from dateutil.relativedelta import relativedelta
from PIL import Image
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError, AccessError
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import url_for
from odoo.tools import sql

from odoo.addons.website_slides.models.slide_slide import Slide as SlideOrigin

def _parse_youtube_document_new(self, document_id, only_preview_fields):
    """ If we receive a duration (YT video), we use it to determine the slide duration.
    The received duration is under a special format (e.g: PT1M21S15, meaning 1h 21m 15s). """

    key = self.env['website'].get_current_website().website_slide_google_app_key
    fetch_res = self._fetch_data('https://www.googleapis.com/youtube/v3/videos', {'id': document_id, 'key': key, 'part': 'snippet,contentDetails', 'fields': 'items(id,snippet,contentDetails)'}, 'json')
    if fetch_res.get('error'):
        return {'error': self._extract_google_error_message(fetch_res.get('error'))}

    values = {'slide_type': 'video', 'document_id': document_id}
    items = fetch_res['values'].get('items')
    if not items:
        return {'error': _('Please enter valid Youtube or Google Doc URL')}
    youtube_values = items[0]

    youtube_duration = youtube_values.get('contentDetails', {}).get('duration')
    if youtube_duration:
        parsed_duration = re.search(r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', youtube_duration)
        if parsed_duration:
            values['completion_time'] = (int(parsed_duration.group(1) or 0)) + \
                                        (int(parsed_duration.group(2) or 0) / 60) + \
                                        (int(parsed_duration.group(3) or 0) / 3600)

    if youtube_values.get('snippet'):
        snippet = youtube_values['snippet']
        if only_preview_fields:
            values.update({
                'url_src': snippet['thumbnails']['high']['url'],
                'title': snippet['title'],
                'description': snippet['description']
            })

            return values

        values.update({
            'name': snippet['title'],
            #'image_1920': self._fetch_data(snippet['thumbnails']['high']['url'], {}, 'image')['values'],
            'description': snippet['description'],
            'mime_type': False,
        })
    return {'values': values}
    

SlideOrigin._parse_youtube_document = _parse_youtube_document_new
