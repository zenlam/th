import json
import time

from werkzeug.urls import url_decode, BytesURL

from odoo.addons.report_xlsx.controllers.main import ReportController
from odoo.http import content_disposition, route, request, \
    serialize_exception as _serialize_exception
from odoo.tools import html_escape
from odoo.tools.safe_eval import safe_eval


class ReportController(ReportController):

    @route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):
        report = request.env['ir.actions.report']._get_report_from_name(reportname)
        if converter == 'text' and not report:

            context = dict(request.env.context)
            if docids:
                docids = [int(i) for i in docids.split(',')]
            if data.get('options'):
                data.update(json.loads(data.pop('options')))
            if data.get('context'):
                # Ignore 'lang' here, because the context in data is the one
                # from the webclient *but* if the user explicitely wants to
                # change the lang, this mechanism overwrites it.
                data['context'] = json.loads(data['context'])
                if data['context'].get('lang'):
                    del data['context']['lang']
                context.update(data['context'])
            context['report_name'] = reportname

            txt = report.with_context(context).render_txt(
                docids, data=data
            )[0]
            report_file = context.get('report_file')
            if not report_file:
                active_model = context.get('active_model', 'export')
                report_file = active_model.replace('.', '_')
            txthttpheaders = [
                ('Content-Type', 'text/plain; charset=utf-8'),
                ('Content-Length', len(txt)),
            ]
            return request.make_response(txt, headers=txthttpheaders)
        return super(ReportController, self).report_routes(
            reportname, docids, converter, **data)

    @route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token):
        """This function is used by 'action_manager_report.js' in order to trigger the download of
        a pdf/controller report.

        :param data: a javascript array JSON.stringified containg report internal url ([0]) and
        type [1]
        :returns: Response with a filetoken cookie and an attachment header
        """
        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]
        try:
            if type in ['qweb-pdf', 'qweb-text']:
                converter = 'pdf' if type == 'qweb-pdf' else 'text'
                extension = 'pdf' if type == 'qweb-pdf' else 'txt'

                pattern = '/report/pdf/' if type == 'qweb-pdf' else '/report/text/'
                reportname = url.split(pattern)[1].split('?')[0]

                docids = None
                if '/' in reportname:
                    reportname, docids = reportname.split('/')

                if docids:
                    # Generic report:
                    response = self.report_routes(reportname, docids=docids,
                                                  converter=converter)
                else:
                    # Particular report:
                    data = url_decode(url.split('?')[
                                          1]).items()  # decoding the args represented in JSON
                    response = self.report_routes(reportname,
                                                  converter=converter,
                                                  **dict(data))

                # get the context from url as a dict
                context_dict = dict(url_decode(url)).get('context')
                # convert string to dict for context
                res = json.loads(context_dict)
                report_id = request.env[res.get('active_model')].browse(res.get('active_id'))
                config_id = request.env['th.file.transfer.config'].search([
                    ('outlet_id', '=', report_id.outlet_id.id),
                    ('period', '=', 'daily')
                ], limit=1)
                txt_format = request.env[
                    'report.gto_summary_report'
                ].get_text_report_format(report_id)
                filename = "%s.%s" % (
                    config_id.name_file.format(**txt_format),
                    extension
                )

                if docids:
                    ids = [int(x) for x in docids.split(",")]
                    obj = request.env[res.get('active_model')].browse(ids)
                    if report_id.print_report_name and not len(obj) > 1:
                        report_name = safe_eval(report_id.print_report_name,
                                                {'object': obj, 'time': time})
                        filename = "%s.%s" % (report_name, extension)
                response.headers.add('Content-Disposition',
                                     content_disposition(filename))
                response.set_cookie('fileToken', token)
                return response
            else:
                return
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
