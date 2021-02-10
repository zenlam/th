odoo.define('th_pos_payment_rounding.models', function (require) {
    "use strict";

    var core = require('web.core');
    var models = require('point_of_sale.models');

    var QWeb = core.qweb;
    var _t = core._t;

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        select_paymentline: function(line){
            // have to override this function due to the logic has to be
            // applied in the middle
            if(line !== this.selected_paymentline){
                if(this.selected_paymentline){
                    this.selected_paymentline.set_selected(false);
                }
                if (line) {
                    if (!line.cashregister.journal.is_rounding_method) {
                        this.selected_paymentline = line;
                    }
                } else {
                    this.selected_paymentline = line;
                }

                if(this.selected_paymentline){
                    this.selected_paymentline.set_selected(true);
                }

                this.trigger('change:selected_paymentline',this.selected_paymentline);
            }
        },
        get_rounding_amount: function (value) {
            if (isNaN(value)) {
                return 0;
            }
            value = value.toFixed(2);
            var res;
            var last_decimal = parseFloat(value).toFixed(2).slice(-1);

            last_decimal = parseInt(last_decimal);
            if (last_decimal == 0 || last_decimal == 5) {
                return 0;
            }
            if (1 <= last_decimal && last_decimal <= 2) {
                return last_decimal / 100
            }
            if (6 <= last_decimal && last_decimal <= 7) {
                return (last_decimal - 5) / 100
            }
            if (3 <= last_decimal && last_decimal <= 4) {
                return (last_decimal - 5) / 100
            }
            if (8 <= last_decimal && last_decimal <= 9) {
                return (last_decimal - 10) / 100
            }
        },
        add_rounding_paymentline: function(cashregister) {
            var existing_lines = this.get_paymentlines();
            this.assert_editable();
            var self = this;

            // create new payment line for rounding
            var roundingPaymentLine = new models.Paymentline({}, {
                order: this,
                cashregister: cashregister,
                pos: this.pos
            });

            // remove the old rounding payment line
            var existingRoundingLine = _.find(this.get_paymentlines(), function (line) {
                return line.cashregister.journal.is_rounding_method;
            });
            if (existingRoundingLine) {
                this.remove_paymentline(existingRoundingLine);
            }

            // get the rounding amount should be tendered and set it to the line
            roundingPaymentLine.set_amount(this.get_rounding_amount(this.get_total_with_tax()), 0);

            // add the payment line to the first position of paymentlines if
            // the rounding amount is non zero
            if (roundingPaymentLine.get_amount()) {
                this.paymentlines.unshift(roundingPaymentLine);
            }

            return roundingPaymentLine;
        },
    });

});