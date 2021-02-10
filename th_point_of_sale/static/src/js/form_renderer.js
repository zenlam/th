odoo.define('th_point_of_sale.FormRenderer', function (require) {
    "use strict";

    var FormRenderer = require('web.FormRenderer');

    FormRenderer.include({

        /**
         *  >>> LAZY HACK by @Siddharth <<<
         *  Override function & add support to add class to node `td`,
         *  when need to change label for single field based on attrs
         *
         *  `div` tag with class `o_td_switch_label` needed
         *  For ex. see `th_point_of_sale/views/product_pricelist_views.xml`
         */

        /**
         * @private
         * @param {Object} node
         * @returns {jQueryElement}
         */
        _renderInnerGroup: function (node) {
            var self = this;
            var $result = $('<table/>', {class: 'o_group o_inner_group'});
            this._handleAttributes($result, node);
            this._registerModifiers(node, this.state, $result);

            var col = parseInt(node.attrs.col, 10) || this.INNER_GROUP_COL;

            if (node.attrs.string) {
                var $sep = $('<tr><td colspan="' + col + '" style="width: 100%;"><div class="o_horizontal_separator">' + node.attrs.string + '</div></td></tr>');
                $result.append($sep);
            }

            var rows = [];
            var $currentRow = $('<tr/>');
            var currentColspan = 0;
            _.each(node.children, function (child) {
                if (child.tag === 'newline') {
                    rows.push($currentRow);
                    $currentRow = $('<tr/>');
                    currentColspan = 0;
                    return;
                }

                var colspan = parseInt(child.attrs.colspan, 10);
                var isLabeledField = (child.tag === 'field' && child.attrs.nolabel !== '1');
                if (!colspan) {
                    if (isLabeledField) {
                        colspan = 2;
                    } else {
                        colspan = 1;
                    }
                }
                var finalColspan = colspan - (isLabeledField ? 1 : 0);
                currentColspan += colspan;

                if (currentColspan > col) {
                    rows.push($currentRow);
                    $currentRow = $('<tr/>');
                    currentColspan = colspan;
                }

                var $tds;
                if (child.tag === 'field') {
                    $tds = self._renderInnerGroupField(child);
                } else if (child.tag === 'label') {
                    $tds = self._renderInnerGroupLabel(child);
                } else if (child.tag === 'div' && child.attrs.class === 'o_td_switch_label') {
                    $tds = $('<td/>', {class: 'o_td_label'}).append(self._renderNode(child));
                } else {
                    $tds = $('<td/>').append(self._renderNode(child));
                }
                if (finalColspan > 1) {
                    $tds.last().attr('colspan', finalColspan);
                }
                $currentRow.append($tds);
            });
            rows.push($currentRow);

            _.each(rows, function ($tr) {
                var nonLabelColSize = 100 / (col - $tr.children('.o_td_label').length);
                _.each($tr.children(':not(.o_td_label)'), function (el) {
                    var $el = $(el);
                    $el.css('width', ((parseInt($el.attr('colspan'), 10) || 1) * nonLabelColSize) + '%');
                });
                $result.append($tr);
            });

            return $result;
        },
    });

});
