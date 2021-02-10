import logging
import psycopg2
from odoo import api, fields, models
from odoo.tools import config, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat

_logger = logging.getLogger(__name__)


class Import(models.TransientModel):
    _inherit = 'base_import.import'

    @api.multi
    def save_mapping(self, fields, columns):
        self.ensure_one()
        base_import_mapping = self.env['base_import.mapping']
        for index, column_name in enumerate(columns):
            if column_name:
                exist_records = base_import_mapping.search(
                    [('res_model', '=', self.res_model), ('column_name', '=', column_name)])
                if exist_records:
                    exist_records.write({'field_name': fields[index]})
                else:
                    base_import_mapping.create({
                        'res_model': self.res_model,
                        'column_name': column_name,
                        'field_name': fields[index]
                    })

        return {}

    @api.multi
    def import_data(self, fields, options, dryrun=False):
        self.ensure_one()
        self._cr.execute('SAVEPOINT import')

        try:
            data, import_fields = self._convert_import_data(fields, options)
            # Parse date and float field
            data = self._parse_import_data(data, import_fields, options)
        except ValueError as error:
            return {
                'messages': [{
                    'type': 'error',
                    'message': pycompat.text_type(error),
                    'record': False,
                }]
            }

        _logger.info('importing %d rows...', len(data))

        name_create_enabled_fields = options.pop('name_create_enabled_fields', {})
        model = self.env[self.res_model].with_context(import_file=True,
                                                      name_create_enabled_fields=name_create_enabled_fields)
        model.load(import_fields, data)
        _logger.info('done')

        try:
            if dryrun:
                self._cr.execute('ROLLBACK TO SAVEPOINT import')
                self.pool.reset_changes()
            else:
                self._cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass


Import()
