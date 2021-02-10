odoo.define('th_pos_payment_rounding.screens', function (require) {
    "use strict";

    var core = require('web.core');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');

    var QWeb = core.qweb;
    var _t = core._t;

    models.load_fields("account.journal", ['is_rounding_method']);

    screens.PaymentScreenWidget.include({
        // populate the rounding payment line upon showing the payment screen
        show: function () {
            this._super();
            var order = this.pos.get_order();
            var rounding_cashregister = _.find(this.pos.cashregisters, function (cashregister) {
                return cashregister.journal.is_rounding_method;
            });

            if (rounding_cashregister) {
                // add the rounding payment line
                order.add_rounding_paymentline(rounding_cashregister);
            }
            this.reset_input();
            this.render_paymentlines();
            this.order_changes();
        },
    });
});