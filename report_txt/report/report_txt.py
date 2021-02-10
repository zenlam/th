from io import StringIO
from odoo import models

import logging
_logger = logging.getLogger(__name__)


class ReportTxtAbstract(models.AbstractModel):
    _name = 'report.report_txt.abstract'
    _description = 'Abstract TXT Report'

    def _get_objs_for_report(self, docids, data):
        """
        Returns objects for xlx report.  From WebUI these
        are either as docids taken from context.active_ids or
        in the case of wizard are in data.  Manual calls may rely
        on regular context, setting docids, or setting data.

        :param docids: list of integers, typically provided by
            qwebactionmanager for regular Models.
        :param data: dictionary of data, if present typically provided
            by qwebactionmanager for TransientModels.
        :param ids: list of integers, provided by overrides.
        :return: recordset of active model for ids.
        """
        if docids:
            ids = docids
        elif data and 'context' in data:
            ids = data["context"].get('active_ids', [])
        else:
            ids = self.env.context.get('active_ids', [])
        return self.env[self.env.context.get('active_model')].browse(ids)

    def create_txt_report(self, docids, data):
        objs = self._get_objs_for_report(docids, data)
        file_data = StringIO()
        self.generate_txt_report(file_data, objs)
        file_data.seek(0)
        return file_data.read(), 'txt'

    def get_workbook_options(self):
        return {}

    def generate_txt_report(self, data, objs):
        raise NotImplementedError()
